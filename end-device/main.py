from machine import SoftI2C, Pin, SPI, reset, idle
from lora import LoRa
import ssd1306
import time
from time import sleep
import socket
import struct
import network
import ubinascii
import uos
import _thread
import uerrno
import sys
import random
import uhashlib

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
wlan = network.WLAN(network.STA_IF)
lora.standby()

# some global variables (values will be overriden later)
mac = "FFFFFFFFFFFF"
dev_id = 1000000
last_seq = -1
_start_experiment = 1
_pkts = 10
_pkt_size = 16
_period = 10
_sf = 7
_rx2sf = 9
_confirmed = 1

### --- FUNCTIONS --- ###
def convert_mac(mac):
    # first 24 bits = OUI
    addr = mac[-6:]
    print("ED id =", addr)
    return int(addr, 16)

def oled_lines(line1, line2, line3, line4):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 10)
    oled.text(line3, 0, 20)
    oled.text(line4, 0, 30)
    oled.show()

def wifi_connect():
    global wlan
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('rasp', 'lalalala')
        while not wlan.isconnected():
            pass

def wait_commands():
    global _start_experiment, _pkts, _pkt_size, _period, _confirmed
    wifi_connect()
    host = wlan.ifconfig()[0]
    port = 8000
    wlan_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wlan_s.bind((host, port))
    wlan_s.listen(5)
    print("Ready...")
    while (True):
        conn, addr = wlan_s.accept()
        data = conn.recv(512)
        if (len(data) > 10):
            try:
                (init, _pkts, _pkt_size, _period, _confirmed) = struct.unpack('BiiiB', data)
                if (init > 0):
                    print("---------------------------------")
                    print("New experiment with", pkts, "packets")
                    _start_experiment = init
            except:
                print("wrong packet format!")

def generate_msg():
    msg = random.getrandbits(32) # just a random 4-byte int
    msg = hex(msg)[2:]
    while (len(msg) < _pkt_size):
        msg = msg + msg
    while (len(msg) > _pkt_size): # just correct the size
        msg = msg[:-1]
    return msg

def random_sleep(max_sleep):
    t = random.getrandbits(32)
    time.sleep(1+t%max_sleep)

def rx_handler(recv_pkg):
    global ack
    if (len(recv_pkg) > 2):
        recv_pkg_len = recv_pkg[1]
        try:
            (gw_id, id, seq) = struct.unpack("iii", recv_pkg)
            print('Received response from', hex(gw_id), dev_id, seq)
            if (id == dev_id) and (seq == last_seq):
                ack = 1
        except:
            print("wrong packet format!")

dev_id = convert_mac(ubinascii.hexlify(wlan.config('mac')).decode())
mac = ubinascii.hexlify(wlan.config('mac')).decode().upper()
mac = ':'.join(mac[i:i+2] for i in range(0,12,2))
oled_lines("LoRa testbed", mac, " ", " ")

# _thread.start_new_thread(wait_commands, ())

while(True):
    # time.sleep(10) # give some time to wifi to connect
    if (_start_experiment):
        print("Random sleep time")
        # random_sleep(_period)
        lora.standby()
        pkts = 1
        delivered = 0
        _start_experiment = 0
        while(pkts <= _pkts and _start_experiment == 0):
            print("-------",pkts,"-------")
            oled_lines("LoRa testbed", mac, str(pkts), " ")
            data = generate_msg()
            cks = uhashlib.sha256(data)
            cks = cks.digest()
            cks = ubinascii.hexlify(cks)
            cks = cks.decode()[:8]
            print("ID =", hex(dev_id), "Data =", data, "Checksum =", int(cks, 16))
            last_seq = pkts
            data = struct.pack('IBII%ds' % len(data), dev_id, len(data), int(cks, 16), pkts, data)
            lora.send(data)
            last_trans = time.ticks_ms()
            print("transmitted at:", last_trans)
            ack = 0
            if (_confirmed):
                time.sleep_ms(990)
                lora.on_recv(rx_handler)
                lora.recv()
                recv_time = time.ticks_ms()
                led.value(1)
                # print("Waiting in RX1 at:", time.ticks_ms())
                while(time.ticks_diff(time.ticks_ms(), recv_time) < 200):
                    if (ack):
                        break
                if (ack):
                    delivered += 1
                    print("RX1 ack received!")
                else:
                    lora.sleep()
                    led.value(0)
                    print("No ack was received in RX1")
                    time.sleep_ms( time.ticks_diff(last_trans+1990, time.ticks_ms()) )
                    lora.set_spreading_factor(_rx2sf)
                    lora.set_frequency(rx2freq)
                    lora.recv()
                    recv_time = time.ticks_ms()
                    led.value(1)
                    # print("Waiting in RX2 at:", time.ticks_ms())
                    while(time.ticks_diff(time.ticks_ms(), recv_time) < 200):
                        if (ack):
                            break
                    if (ack):
                        delivered += 1
                        print("RX2 ack received!")
                    else:
                        pkts -= 1
                        print("No ack was received in RX2")
            lora.set_spreading_factor(_sf)
            lora.set_frequency(freqs[0])
            led.value(0)
            lora.sleep()
            pkts += 1
            # watch duty cycle violations here
            time.sleep_ms(_period*1000)
            random_sleep(2) # sleep for some random time as well
        # TODO: send statistics
