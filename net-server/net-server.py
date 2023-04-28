#!/usr/bin/python3

import socket
import threading
import struct
import time
import math

bind_ip = '192.168.1.230'
bind_port = 8001

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(10)

next_dc = {}
next_dc[1] = time.time()
next_dc[2] = time.time()
rx2sf = 9
mutex = threading.Lock()

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
    return (Tpream + Tpayload)/1000 # this will return secs!

def handle_client_connection(client_socket):
    global next_dc
    request = client_socket.recv(512)
    recv_time = time.time()
    try:
        (gid, nid, seq, sf) = struct.unpack('IIIB', request)
        print ("Received from:", hex(gid), seq, sf)
    except Exception as e:
        print ("Could not unpack", e)
    else:
        # check duty cycle and RW availability
        rw = 0
        if (recv_time+1 > next_dc[1]):
            rw = 1
            airt = airtime(sf,1,12,125)
            mutex.acquire()
            next_dc[1] = recv_time + rw + 99*airt
            print ("Scheduled", hex(gid), seq, sf, "for RW1")
            mutex.release()
        elif (recv_time+2 > next_dc[2]):
            rw = 2
            airt = airtime(rx2sf,1,12,125)
            mutex.acquire()
            next_dc[2] = recv_time + rw + 9*airt
            print ("Scheduled", hex(gid), seq, sf, "for RW2")
            mutex.release()
        else:
            print ("No resources available for", hex(gid), "SF", sf)
        resp = struct.pack('IIIB', gid, nid, seq, rw)
        client_socket.send(resp)
        client_socket.close()

while True:
    client_sock, address = server.accept()
    #print ("Accepted connection from:", address[0], address[1])
    client_handler = threading.Thread(
        target=handle_client_connection,
        args=(client_sock,)
    )
    client_handler.start()
