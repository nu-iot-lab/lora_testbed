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
wlan = network.WLAN(network.STA_IF)

# some global variables (values will be overriden later)
mac = "FFFFFFFFFFFF"
gw_id = 1000000
schedule = []
next_rx1 = 0.0
next_rx2 = 0.0
next_duty_cycle = {}
next_duty_cycle[1] = 0.0
next_duty_cycle[2] = 1.0
_sf = 7
_rx2sf = 9

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

def wait_commands():
    global lora, _sf, _rx2sf, schedule, next_rx1, next_rx2, next_duty_cycle, airt1, airt2
    wifi_connect()
    webrepl.start()
    host = wlan.ifconfig()[0]
    port = 8000
    wlan_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wlan_s.setblocking(False)
    wlan_s.bind((host, port))
    wlan_s.listen(5)
    print("Ready...")
    poller = select.poll()
    poller.register(wlan_s, select.POLLIN)
    while (True):
        while (True):
            events = poller.poll()
            #print('events = ', events)
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
                    schedule = []
                    next_rx1 = 0.0
                    next_rx2 = 0.0
                    next_duty_cycle = {}
                    next_duty_cycle[1] = 0.0
                    next_duty_cycle[2] = 1.0
                    lora.sleep()
                    lora.set_spreading_factor(_sf)
                    lora.set_frequency(freqs[0])
                    lora.recv()
                    airt1 = airtime(_sf,1,12,125)
                    airt2 = airtime(_rx2sf,1,12,125)
            except Exception as e:
                print("wrong packet format!", e)

def permitted(ti, w):
    if (w == 1):
        if (ti < next_duty_cycle[1]):
            print("No duty cycle resources available in RX1")
            return 0
        tj = ti + airt1
        t1 = next_rx2
        t2 = t1 + airt2
        if ( (ti >= t1 and ti <= t2) or (tj <= t2 and tj >= t1) or (ti == t1 and tj == t2) ):
            return 0
    else:
        if (ti < next_duty_cycle[2]):
            print("No duty cycle resources available in RX2")
            return 0
        tj = ti + airt2
        t1 = next_rx1
        t2 = t1 + airt1
        if ( (ti >= t1 and ti <= t2) or (tj <= t2 and tj >= t1) or (ti == t1 and tj == t2) ):
            return 0
    return 1

def rx_handler(recv_pkg):
    global schedule, next_duty_cycle, next_rx1, next_rx2
    if (len(recv_pkg) > 4):
        recv_pkg_len = recv_pkg[4]
        # print(recv_pkg_len)
        try:
            print("---")
            (dev_id, leng, cks, seq, msg) = struct.unpack('IBII%ds' % recv_pkg_len, recv_pkg)
            recv_time = time.ticks_ms()
            print("Received from:", hex(dev_id), leng, cks, seq, msg, "at", recv_time, lora.get_rssi())
            msg = msg.decode()
            cks_ = uhashlib.sha256(msg)
            cks_ = cks_.digest()
            cks_ = ubinascii.hexlify(cks_)
            cks_ = cks_.decode()[:8]
            # print(msg, cks_, cks)
            if (int(cks_,16) == cks):
                # schedule an ack if the ack does not collide with other transmissions and there are available resources
                if (permitted(recv_time+1000, 1) == 1):
                    schedule.append([recv_time+1000, dev_id, seq, 1])
                    next_rx1 = recv_time+1000
                elif (permitted(recv_time+1000, 2) == 1):
                    schedule.append([recv_time+2000, dev_id, seq, 2])
                    next_rx2 = recv_time+2000
                else:
                    print("Gateway unavailable!")
            else:
                print("Checksum not valid!")
        except Exception as e:
            print("wrong packet format!", e)

def scheduler():
    global lora, schedule, next_duty_cycle
    while(1):
        if len(schedule) > 0:
            try:
                (tm, dev_id, seq, win) = schedule[0]
                if (tm < time.ticks_ms() or tm < next_duty_cycle[win]):
                    print("skipping transmission")
                    schedule.remove(schedule[0])
                    continue
                print("picked up", tm, dev_id, seq, win)
                ack_pkt = struct.pack('iii', gw_id, dev_id, seq)
                if (win == 2):
                    lora.sleep()
                    lora.set_spreading_factor(_rx2sf)
                    lora.set_frequency(rx2freq)
                    lora.standby()
                while(time.ticks_diff(tm, time.ticks_ms()) > 0):
                    idle()
                print("Sending ack to", hex(dev_id), "at", time.ticks_ms(), "( RX", win, ")")
                lora.send(ack_pkt)
                lora.sleep()
                if (win == 1):
                    next_duty_cycle[1] = time.ticks_ms()+99*airt1
                elif (win == 2):
                    next_duty_cycle[2] = time.ticks_ms()+9*airt2
                    lora.set_spreading_factor(_sf)
                    lora.set_frequency(freqs[0])
                schedule.remove(schedule[0])
                lora.recv()
            except Exception as e:
                print("Something went wrong in scheduling", e)

airt1 = airtime(_sf,1,12,125)
airt2 = airtime(_rx2sf,1,12,125)
gw_id = convert_mac(ubinascii.hexlify(wlan.config('mac')).decode())
lora.on_recv(rx_handler)
lora.recv()

_thread.start_new_thread(wait_commands, ())
_thread.start_new_thread(scheduler, ())
