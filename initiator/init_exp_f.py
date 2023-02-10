#!/usr/bin/python3

import socket
import sys
import struct
import random


PORT = 8000
BUFFER_SIZE = 512
assets = []
eds = 0
init = random.randint(1, 65535)

with open("assets.txt") as file:
	next(file)
	assets = [l.rstrip() for l in file]

# if the argument is 'U'
# 	-> send webrepl command to each device (ED / GW)
# 	-> wait 30" and then continue
# else continue

for asset in assets:
	MESSAGE = bytes(0)
	print(asset)
	items = asset.split(" ")
	IP = items[1]
	if (items[0] == 'GW'):
		MESSAGE = struct.pack('HBB', init, int(items[2]), int(items[3]))
	elif (items[0] == 'ED'):
		eds += 1
		MESSAGE = struct.pack('HiiiBBB', init, int(items[2]), int(items[3]), int(items[4]), int(items[5]), int(items[6]), int(items[7]))
	else:
		continue
	print("Sending to", items[0])
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((IP, PORT))
		s.send( MESSAGE )
		s.close()
	except:
		print("Socket error!")


print("\nWaiting for statistics\n")
f = open("stats.txt", "w")
a = 0
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('192.168.1.230', PORT))
s.listen(50)
while (a < eds):
	(conn, addr) = s.accept()
	data = conn.recv(512)
	if (len(data) > 10):
		try:
			(id, deliv, fail, rssi) = struct.unpack('IIIf', data)
			print(hex(id), deliv, fail, rssi)
			f.write( "%s: %s %s %s\n" % ( hex(id), str(deliv), str(fail), str(rssi) ) )
			a += 1
		except:
			print("wrong stat packet format!")
f.close()
