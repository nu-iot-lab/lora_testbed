from machine import SoftI2C, Pin, SPI, reset, freq
from lora import LoRa
import ssd1306
import time
import socket
import struct
import network
import ubinascii
import _thread
import random
import uhashlib
import webrepl
import select
import esp32

# freq(80000000)
# led = Pin(25,Pin.OUT) # heltec V2
led = Pin(2,Pin.OUT) # TTGO
rst = Pin(16, Pin.OUT)
rst.value(1)
scl = Pin(15, Pin.OUT, Pin.PULL_UP)
sda = Pin(4, Pin.OUT, Pin.PULL_UP)
i2c = SoftI2C(scl=scl, sda=sda, freq=450000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)
oled.poweron()
oled.fill(0)
oled.text("LoRa testbed", 0, 0)
oled.show()

# SPI pins
SCK  = 5
MOSI = 27
MISO = 19
CS   = 18
RX   = 26

# Setup SPI
spi = SPI(
    1,
    baudrate=1000000,
    sck=Pin(SCK, Pin.OUT, Pin.PULL_DOWN),
    mosi=Pin(MOSI, Pin.OUT, Pin.PULL_UP),
    miso=Pin(MISO, Pin.IN, Pin.PULL_UP),
)
spi.init()

# Setup LoRa
lora = LoRa(
    spi,
    cs=Pin(CS, Pin.OUT),
    rx=Pin(RX, Pin.IN),
)

# some settings
freqs = [868.1, 868.3, 868.5, 867.1, 867.3, 867.5, 867.7, 867.9]
rx2freq = 869.525
lora.set_spreading_factor(7)
lora.set_frequency(freqs[0])
lora.set_crc(True)
wlan = network.WLAN(network.STA_IF)
lora.standby()

# some global variables (values will be overriden later)
mac = "FFFFFFFFFFFF"
dev_id = 1000000
last_seq = -1
init = 0
_start_experiment = 0
_exp_time = 3600
_pkt_size = 16
_period = 10
_sf = 7
_rx2sf = 9
_confirmed = 1
max_retries = 1
tx_time = 0.0
rx_time = 0.0
rwone = 0
rwtwo = 0

### --- FUNCTIONS --- ###
def random_sleep(max_sleep):
    t = random.getrandbits(32)
    time.sleep(1+t%max_sleep)

def convert_mac(mac):
    # first 24 bits = OUI
    addr = mac[-6:]
    print("ED id =", addr)
    return int(addr, 16)

def oled_lines(line1, line2, line3, line4, line5):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 15)
    oled.text(line3, 0, 25)
    oled.text(line4, 0, 35)
    oled.text(line5, 0, 45)
    oled.show()

def wifi_connect():
    global wlan
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
	random_sleep(10)
        wlan.connect('IoTLab', '97079088')
        while not wlan.isconnected():
            pass

def wait_commands():
    global init, lora, _start_experiment, _exp_time, _sf, _rx2sf, _pkt_size, _period, _confirmed, wlan_s
    wifi_connect()
    webrepl.start()
    time.sleep(5)
    host = wlan.ifconfig()[0]
    port = 8002
    wlan_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wlan_s.setblocking(False)
    wlan_s.bind((host, port))
    wlan_s.listen(5)
    print("Ready...")
    led.value(1)
    oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "ED", " ")
    poller = select.poll()
    poller.register(wlan_s, select.POLLIN)
    while (True):
        while (True):
            events = poller.poll()
            #print('events = ', events)
            if events is not None:
                break
        conn, addr = wlan_s.accept()
        print(addr)
        data = conn.recv(512)
        if (len(data) > 2):
            try:
                (init, _exp_time, _pkt_size, _period, _sf, _rx2sf, _confirmed) = struct.unpack('HiiiBBB', data)
                if (init > 0):
                    print("---------------------------------")
                    print("New experiment for", _exp_time, "secs and SF", _sf)
                    oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "ED", str(init))
                    lora.sleep()
                    lora.set_spreading_factor(_sf)
                    lora.set_frequency(freqs[0])
                    lora.standby()
                    _start_experiment = init
            except Exception as e:
                print("wrong packet format!", e)

def generate_msg():
    msg = random.getrandbits(32) # just a random 4-byte int
    msg = hex(msg)[2:]
    while (len(msg) < _pkt_size):
        msg = msg + msg
    while (len(msg) > _pkt_size): # just correct the size
        msg = msg[:-1]
    return msg

def rx_handler(recv_pkg):
    global ack, rssi
    if (len(recv_pkg) > 2):
        recv_pkg_len = recv_pkg[1]
        try:
            (gw_id, id, seq) = struct.unpack("iii", recv_pkg)
            print('Received response from', hex(gw_id), dev_id, seq)
            if (id == dev_id) and (seq == last_seq):
                rssi += lora.get_rssi()
                ack = 1
        except Exception as e:
            print("wrong GW packet format!", e)

dev_id = convert_mac(ubinascii.hexlify(wlan.config('mac')).decode())
mac = ubinascii.hexlify(wlan.config('mac')).decode().upper()
mac = ':'.join(mac[i:i+2] for i in range(0,12,2))
print("MAC =", mac)
oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "ED", " ")

_thread.start_new_thread(wait_commands, ())

while(True):
    if (_start_experiment):
        start_exp = time.time()
        print("Random sleep time")
        random_sleep(_period)
        lora.standby()
        pkts = 1
        delivered = 0
        retransmitted = 0
        failed = 0
        rssi = 0.0
        tx_time = 0.0
        rx_time = 0.0
        rwone = 0
        rwtwo = 0
        _start_experiment = 0
        led.value(0)
        f = 0
        retries = 0
        runn = 1
        while(runn == 1 and _start_experiment == 0):
            print("------- Packets:", pkts, "Elapsed time:", time.time()-start_exp, "/", _exp_time, "-------")
            oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "ED", str(init)+" "+str(pkts))
            if (f == 0):
                data = generate_msg()
            cks = uhashlib.sha256(data)
            cks = cks.digest()
            cks = ubinascii.hexlify(cks)
            cks = cks.decode()[:8]
            print("ID =", hex(dev_id), "Data =", data, "Checksum =", int(cks, 16))
            last_seq = pkts
            pkt = struct.pack('IBII%ds' % len(data), dev_id, len(data), int(cks, 16), pkts, data)
            tm = time.ticks_us()
            lora.send(pkt)
            tx_time += time.ticks_us()-tm
            last_trans = time.ticks_ms()
            print("transmitted at:", last_trans)
            ack = 0
            if (_confirmed):
                time.sleep_ms(990)
                lora.on_recv(rx_handler)
                lora.recv_once()
                recv_time = time.ticks_ms()
                led.value(1)
                print("Waiting in RX1 at:", time.ticks_ms())
                timeout = 140*(_sf-7+1)
                tm = time.ticks_us()
                while(time.ticks_diff(time.ticks_ms(), recv_time) < timeout):
                    if (lora._get_irq_flags()): # check if something is being received (RxTimeout should be used)
                        timeout += 400
                    if (ack):
                        break
                rx_time += time.ticks_us()-tm
                if (ack):
                    delivered += 1
                    retries = 0
                    f = 0
                    rwone += 1
                    print("RX1 ack received!")
                else:
                    lora.sleep()
                    led.value(0)
                    print("No ack was received in RX1")
                    if (_rx2sf < _sf):
                        print("RX2 SF higher than uplink SF")
                    else:
                        time.sleep_ms( time.ticks_diff(last_trans+1990, time.ticks_ms()) )
                        lora.set_spreading_factor(_rx2sf)
                        lora.set_frequency(rx2freq)
                        lora.recv_once()
                        recv_time = time.ticks_ms()
                        led.value(1)
                        print("Waiting in RX2 at:", time.ticks_ms())
                        timeout = 500
                        tm = time.ticks_us()
                        while(time.ticks_diff(time.ticks_ms(), recv_time) < timeout):
                            if (ack):
                                break
                        if (ack):
                            delivered += 1
                            retries = 0
                            f = 0
                            rwtwo += 1
                            print("RX2 ack received!")
                        else:
                            f = 1
                            print("No ack was received in RX2")
                        rx_time += time.ticks_us()-tm
            lora.set_spreading_factor(_sf)
            lora.set_frequency(freqs[0])
            led.value(0)
            lora.sleep()
            pkts += 1
            if (time.time() - start_exp < _exp_time) and (f == 0): # just skip the last sleep time
                # watch for duty cycle violations here
                time.sleep_ms(_period*1000)
                random_sleep(1) # sleep for some random time as well
            elif (time.time() - start_exp < _exp_time) and (f == 1):
                if (retries < max_retries):
                    pkts -= 1
                    retries += 1
                    retransmitted += 1
                    random_sleep(5) # in case of a failure -> retransmit (TODO: follow duty cycle rules)
                else:
                    retries = 0
                    failed += 1
                    f = 0
            if (time.time() - start_exp >= _exp_time):
                runn = 0

        if (_start_experiment == 0):
            print("I am sending stats...")
            random_sleep(10)
            rx_time /= 1e6
            tx_time /= 1e6
            if delivered > 0:
                rssi /= delivered
            stat_pkt = struct.pack('IBIIIfffii', dev_id, _sf, delivered, retransmitted, failed, rssi, tx_time, rx_time, rwone, rwtwo)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('192.168.1.230', 8002))
                s.send(stat_pkt)
                s.close()
            except Exception as e:
                print("Couldn't send out stats", e)
            time.sleep(5)
            reset()
