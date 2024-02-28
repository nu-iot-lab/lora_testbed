from machine import SoftI2C, Pin, SPI, reset, RTC
from lora import LoRa
import ssd1306
import time
import socket
import struct
import network
import ubinascii
import _thread
import uerrno
import random
import uhashlib
import math
import webrepl
import select

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

# some global variables (values will be overriden later)
mac = "FFFFFFFFFFFF"
gw_id = 1000000 # will be set up later
schedule = []
_sf = 7 # default value
_rx2sf = 9
received = 0

rtc = RTC()

### --- FUNCTIONS --- ###
def convert_mac(mac):
    # first 24 bits = OUI
    addr = mac[-6:]
    print("Gateway id =", addr)
    return int(addr, 16)

def oled_lines(line1, line2, line3, line4, line5):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 15)
    oled.text(line3, 0, 25)
    oled.text(line4, 0, 35)
    oled.text(line5, 0, 45)
    oled.show()

def random_sleep(max_sleep):
    t = random.getrandbits(32)
    time.sleep(1+t%max_sleep)

def wifi_connect():
    global wlan, mac, gw_id
    wlan.active(True)
    mac = ubinascii.hexlify(wlan.config('mac')).decode().upper()
    mac = ':'.join(mac[i:i+2] for i in range(0,12,2))
    print("MAC address:", mac)
    if not wlan.isconnected():
        print('connecting to network...')
        random_sleep(10)
        wlan.connect('IoTLab', '97079088')
        while not wlan.isconnected():
            time.sleep(1)
    oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "GW", " ")

def wait_commands():
    global lora, _sf, _rx2sf, schedule, received
    wifi_connect()
    webrepl.start()
    host = wlan.ifconfig()[0]
    wlan_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wlan_s.setblocking(False)
    wlan_s.bind((host, 8002))
    wlan_s.listen(5)
    print("Ready...")
    poller = select.poll()
    poller.register(wlan_s, select.POLLIN)
    while (True):
        while (True):
            events = poller.poll()
            if events is not None:
                break
        conn, addr = wlan_s.accept()
        data = conn.recv(512)
        if (len(data) > 2):
            try:
                (init, _sf, _rx2sf) = struct.unpack('HBB', data)
                if (init > 0):
                    print("---------------------------------")
                    print("New experiment with SF", _sf, "and RX2SF", _rx2sf)
                    oled_lines("LoRa testbed", mac[2:], wlan.ifconfig()[0], "GW", str(init))
                    lora.sleep()
                    schedule = []
                    lora.set_spreading_factor(_sf)
                    lora.set_frequency(freqs[0])
                    lora.recv()
                    received = 0
            except Exception as e:
                print("wrong packet format!", e)

def rx_handler(recv_pkg):
    global schedule, received
    if (len(recv_pkg) > 4):
        recv_pkg_len = recv_pkg[4]
        recv_time = time.time_ns()
        internal_recv = time.ticks_ms()
        try:
            print("---")
            (dev_id, leng, sux_tx, cks, seq, cnfrm, msg) = struct.unpack('IBBIHB%ds' % recv_pkg_len, recv_pkg)
            rss = lora.get_rssi()
            print("Received from:", hex(dev_id), leng, sux_tx, cks, seq, cnfrm, msg, "at", recv_time, rss)
            msg = msg.decode()
            cks_ = uhashlib.sha256(msg)
            cks_ = cks_.digest()
            cks_ = ubinascii.hexlify(cks_)
            cks_ = cks_.decode()[:8]
            if (int(cks_,16) == cks):
                received += 1
                # send data to net-server
                try:
                    wlan_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    wlan_s.connect(('192.168.0.230', 8001))
                except Exception as e:
                    print("Connection to NS failed!", e)
                    wlan_s.close()
                else:
                    pkg = struct.pack('IIHBBBQi', gw_id, int(dev_id), seq, sux_tx, _sf, cnfrm, recv_time, rss)
                    wlan_s.send(pkg)
                    if int(cnfrm) == 1:
                        msg = wlan_s.recv(512)
                        win = 0
                        try:
                            (rgw_id, rdev_id, rseq, win) = struct.unpack('IIIB', msg)
                            print("Received from NS:", rgw_id, rdev_id, rseq, win)
                        except Exception as e:
                            print("wrong NS packet format!", e)
                            wlan_s.close()
                            led.value(0)
                        else:
                            if (rgw_id == gw_id) and (rdev_id == dev_id) and (rseq == seq):
                                if (win > 0):
                                    el = internal_recv+int(win)*1e3
                                    print(el)
                                    schedule.append([el, dev_id, seq, int(win)])
                                    print("RW"+str(win)+" ok")
                                else:
                                    print("Gateway unavailable!")
                            wlan_s.close()
            else:
                print("Checksum not valid!")
        except Exception as e:
            print("wrong packet format!", e)

def scheduler():
    global lora, schedule
    while True:
        time.sleep(0.1)
        if len(schedule) > 0:
            try:
                (tm, dev_id, seq, win) = schedule[0]
                if (tm < time.ticks_ms()):
                    print("skipping transmission")
                    schedule.remove(schedule[0])
                    continue
                print("Picked up", tm, dev_id, seq, win)
                ack_pkt = struct.pack('III', gw_id, dev_id, seq)
                if (win == 2):
                    lora.set_spreading_factor(_rx2sf)
                    lora.set_frequency(rx2freq)
                    lora.standby()
                while(tm - time.ticks_ms() > 0):
                    pass
                print("...sending ack to", hex(dev_id), "at", time.time_ns(), "( RW", win, ")")
                lora.send(ack_pkt)
                if (win == 2):
                    lora.set_spreading_factor(_sf)
                    lora.set_frequency(freqs[0])
                schedule.remove(schedule[0])
                lora.recv()
                print("......done")
            except Exception as e:
                print("Something went wrong in scheduling", e)
                lora.recv()

def get_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo("pool.ntp.org", 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - 3155673600

def set_time():
    t = get_time()
    tm = time.localtime(t+6*60*60) # KZ
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    rtc.datetime(tm)
    # print(time.localtime())

def ntp_sync():
    while(True):
        try:
            set_time()
            print("Time sync done")
        except:
            pass
        time.sleep(20)

gw_id = convert_mac(ubinascii.hexlify(wlan.config('mac')).decode())
lora.on_recv(rx_handler)
lora.recv()

_thread.start_new_thread(wait_commands, ())
time.sleep(10)
_thread.start_new_thread(ntp_sync, ())
_thread.start_new_thread(scheduler, ())
