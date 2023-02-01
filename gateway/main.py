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
import math

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

# some global variables (values will be overriden later)
mac = "FFFFFFFFFFFF"
gw_id = 1000000
schedule = []
next_avail_slot = 0.0
next_duty_cycle = {}
next_duty_cycle[1] = 0.0
next_duty_cycle[2] = 1.0
_sf = 7
_rx2sf = 9

### --- FUNCTIONS --- ###
def convert_mac(mac):
    # first 24 bits = OUI
    addr = mac[-6:]
    print(addr)
    return int(addr, 16)

def oled_lines(line1, line2, line3, line4):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 10)
    oled.text(line3, 0, 20)
    oled.text(line4, 0, 30)
    oled.show()

def wifi_connect():
    global wlan, mac, gw_id
    wlan.active(True)
    mac = ubinascii.hexlify(wlan.config('mac')).decode().upper()
    gw_id = convert_mac(mac)
    mac = ':'.join(mac[i:i+2] for i in range(0,12,2))
    print("MAC address:", mac)
    oled_lines("LoRa testbed", mac, " ", " ")
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('rasp', 'lalalala')
        while not wlan.isconnected():
            pass

# this is borrowed from LoRaSim (https://www.lancaster.ac.uk/scc/sites/lora/lorasim.html)
def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8
    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1
    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload


def rx_handler(recv_pkg):
    global schedule, next_avail_slot, next_duty_cycle
    if (len(recv_pkg) > 2):
        recv_pkg_len = recv_pkg[4]
        print(recv_pkg_len)
        try:
            (dev_id, leng, cks, seq, msg) = struct.unpack('IBII%ds' % recv_pkg_len, recv_pkg)
            print(dev_id, leng, cks, seq, msg)
            recv_time = time.ticks_ms()
            msg = msg.decode()
            cks_ = uhashlib.sha256(msg)
            cks_ = cks_.digest()
            cks_ = ubinascii.hexlify(cks_)
            cks_ = cks_.decode()[:8]
            print(msg, cks_, cks)
            if (int(cks_,16) == cks):
                # schedule an ack if the ack does not collide with other transmissions and there are available resources
                if (recv_time+1000 > next_avail_slot) and (next_duty_cycle[1] <= recv_time+1000):
                    airt = airtime(_sf,1,12,125)
                    schedule.append([recv_time+1000, dev_id, seq, 1])
                    next_avail_slot = recv_time + 1000 + airt
                elif (recv_time+2000 > next_avail_slot) and (next_duty_cycle[2] <= recv_time+2000):
                    airt = airtime(_rx2sf,1,12,125)
                    schedule.append([recv_time+2000, dev_id, seq, 2])
                else:
                    print("Gateway unavailable!")
            else:
                print("Checksum not valid!")
        except:
            print("wrong packet format!")

def scheduler():
    global schedule, next_duty_cycle
    while(1):
        if len(schedule) > 0:
            (tm, dev_id, seq, win) = schedule[0]
            print("picked up", tm, dev_id, seq, win)
            ack_pkt = struct.pack('iii', gw_id, dev_id, seq)
            while(time.ticks_diff(tm, time.ticks_ms()) > 0):
                idle()
            if (win == 2):
                lora.set_spreading_factor(_rx2sf)
                lora.set_frequency(rx2freq)
            print("Sending ack at", time.ticks_ms(), "(", tm, ")")
            lora.send(ack_pkt)
            if (win == 1):
                next_duty_cycle[1] = time.ticks_ms()+99*airtime(_sf,1,12,125)
            elif (win == 2):
                next_duty_cycle[2] = time.ticks_ms()+9*airtime(_rx2sf,1,12,125)
            schedule.remove(schedule[0])
            lora.recv()

lora.on_recv(rx_handler)
lora.recv()

_thread.start_new_thread(scheduler, ())
