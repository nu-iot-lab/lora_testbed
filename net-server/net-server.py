#!/usr/bin/python3

import socket
import threading
import struct
import time
import math

bind_ip = '192.168.1.230'
bind_port = 8001

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((bind_ip, bind_port))
server.listen(10)

next_dc = {} # next available radio duty cycle per window
next_dc[1] = 0
next_dc[2] = 0
rx2sf = 9 # default value
mutex = threading.Lock() # only 1 gw has access to transmitting resources
next_transm = 0 # it is used to avoid having two or more gws transmitting at the same time
downlinks = [] # holds downlink tuples (start, end) of transmission

def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8
    if bw == 125 and sf in [11, 12]:
        DE = 1
    if sf == 6:
        H = 1
    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return (Tpream + Tpayload)*1e6 # convert to ns

def handle_client_connection(client_socket):
    global next_dc, next_transm, downlinks, mutex, rx2sf
    request = client_socket.recv(512)
    if (len(request) == 3):
        try:
            (init, rx2sf) = struct.unpack('HB', request)
        except Exception as e:
            print ("["+str(time.time())+"]:", "Could not unpack", e)
        else:
            print("-------------------------------------------------")
            print("["+str(time.time())+"]:", "New experiment with id", init, "and RX2SF", rx2sf)
            rx2sf = int(rx2sf)
            next_dc[1] = 0
            next_dc[2] = 0
            next_transm = 0
            downlinks = []
            if mutex.locked() == True:
                mutex.release()
    else:
        try:
            (gid, nid, seq, sf, recv_time) = struct.unpack('IIIBQ', request)
            print ("["+str(time.time())+"]:", "Received from:", hex(gid), seq, sf, recv_time)
        except Exception as e:
            print ("["+str(time.time())+"]:", "Could not unpack", e)
        else:
            # check duty cycle and transmission availability
            rw = 0
            clash = 0
            for dl in downlinks:
                if (recv_time > dl[0] and recv_time < dl[1]): # cannot accept uplinks during downlink time
                    clash = 1
                if (dl[1] + 5*1e9 < recv_time): # keep items in the list for 5sec min
                    downlinks.remove(dl)
            if clash == 0:
                mutex.acquire(timeout=2)
                if (recv_time+1*1e9 >= next_dc[1]):
                    rw = 1
                    airt = airtime(sf,1,12,125)
                    if (recv_time+rw*1e9+airt > next_transm):
                        next_dc[1] = recv_time + rw*1e9 + 99*airt
                        next_transm = recv_time+rw*1e9+airt
                        downlinks.append([recv_time+rw*1e9, recv_time+rw*1e9+airt])
                        print ("["+str(time.time())+"]:", "Scheduled", hex(gid), seq, sf, "for RW1")
                else:
                    if (recv_time+2*1e9 >= next_dc[2]):
                        rw = 2
                        airt = airtime(rx2sf,1,12,125)
                        if (recv_time+rw*1e9+airt > next_transm):
                            next_dc[2] = recv_time + rw*1e9 + 9*airt
                            next_transm = recv_time+rw*1e9+airt
                            downlinks.append([recv_time+rw*1e9, recv_time+rw*1e9+airt])
                            print ("["+str(time.time())+"]:", "Scheduled", hex(gid), seq, sf, "for RW2")
                    else:
                        print ("["+str(time.time())+"]:", "No resources available for", hex(gid), "SF", sf)
            else:
                print ("["+str(time.time())+"]:", "Uplink clash for", hex(gid), "SF", sf)
            resp = struct.pack('IIIB', gid, nid, seq, rw)
            client_socket.send(resp)
            if mutex.locked() == True:
                mutex.release()
            client_socket.close()
            print ("Downlinks in queue:", len(downlinks))

while True:
    client_sock, address = server.accept()
    #print ("Accepted connection from:", address[0], address[1])
    client_handler = threading.Thread(
        target=handle_client_connection,
        args=(client_sock,)
    )
    client_handler.start()
