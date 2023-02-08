#!/usr/bin/python3

import socket
import sys
import struct
import random

if (len(sys.argv) < 6):
	print("./init_exp.py <pkts> <pkt_size> <period> <sf> <rx2sf> <confirmed>")
	sys.exit()

init = random.randint(1, 65535)
_pkts = int(sys.argv[1]) # packets to send per node [1..inf]
_pkt_size = int(sys.argv[2]) # packets size [16..240]
_period = int(sys.argv[3]) # period between transmissions [1..inf]
_sf = int(sys.argv[4]) # SF for uplinks [7..12]
_rx2sf = int(sys.argv[5]) # RX2 SF [7..12]
_confirmed = int(sys.argv[6]) # confirmed/unconfirmed (0/1)

gws = ['192.168.0.43', '192.168.0.44']
eds = ['192.168.0.40', '192.168.0.41', '192.168.0.42', '192.168.0.45', '192.168.0.46']

PORT = 8000
BUFFER_SIZE = 512

for gw in gws:
	print("Sending to", gw)
	IP = gw
	MESSAGE = struct.pack('HBB', init, _sf, _rx2sf)
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((IP, PORT))
		#s.send( bytes( MESSAGE.encode('utf-8') ) )
		s.send( MESSAGE )
		s.close()
	except:
		print("Socket error!")

for ed in eds:
	print("Sending to", ed)
	IP = ed
	MESSAGE = struct.pack('HiiiBBB', init, _pkts, _pkt_size, _period, _sf, _rx2sf, _confirmed)
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((IP, PORT))
		#s.send( bytes( MESSAGE.encode('utf-8') ) )
		s.send( MESSAGE )
		s.close()
	except:
		print("Socket error!")

