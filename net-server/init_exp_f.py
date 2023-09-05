#!/usr/bin/python3

import socket
import sys
import struct
import random
import subprocess
import shlex
import time

if len(sys.argv) < 3:
	print("python3 init_exp_f.py -m <U/C>")
	sys.exit()

PORT = 8002
BUFFER_SIZE = 512
assets = []
eds = 0
init = random.randint(1, 65535)
passwd = "97079088"

with open("assets.txt") as file:
	next(file)
	assets = [l.rstrip() for l in file]


for i in range(len(sys.argv)):
	if sys.argv[i] == '-m':
		sys.argv.pop(i)
		mode = sys.argv.pop(i)
		break


if mode == 'U':
	for asset in assets:
		items = asset.split(" ")
		print(asset)
		IP = items[1]
		reboot_command = 'python3 webrepl/webrepl_client.py -p 97079088 '+str(IP)+' < <(echo -e "import machine" && echo -e "machine.reset()" && echo -e "exit")'
		if (items[0] == 'GW'):
			src_file = "../gateway/main.py"
			remote_path = IP + ":/" + "main.py"
			cmd = ['python3', 'webrepl/webrepl_cli.py', '-p', passwd, src_file, remote_path]
			p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
			for line in p.stdout:
				print(line.decode("utf-8"))
			p.wait()
			reboot_process = subprocess.Popen(reboot_command, shell = True, stdout = subprocess.PIPE, executable='/bin/bash')
			time.sleep(2)
			reboot_process.kill()
		elif (items[0] == 'ED'):
			src_file = "../end-device/main.py"
			remote_path = IP + ":/" + "main.py"
			cmd = ['python3', 'webrepl/webrepl_cli.py', '-p', passwd, src_file, remote_path]
			p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
			for line in p.stdout:
				print(line.decode("utf-8"))
			p.wait()
			reboot_process = subprocess.Popen(reboot_command, shell = True, stdout = subprocess.PIPE, executable='/bin/bash')
			time.sleep(2)
			reboot_process.kill()
		else:
			continue
	time.sleep(10)
elif mode == 'C':
	rx2sf = 9
	print("\nNew experiment with id:", init)
	# contact all GWs and EDs
	for asset in assets:
		MESSAGE = bytes(0)
		print(asset)
		items = asset.split(" ")
		IP = items[1]
		if (items[0] == 'GW'):
			MESSAGE = struct.pack('HBB', init, int(items[2]), int(items[3]))
			rx2sf = int(items[3])
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
		except Exception as e:
			print("Socket error!", e)
	# contact the NS as well to update rx2sf
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('192.168.1.230', 8001))
		MESSAGE = struct.pack('HB', init, rx2sf)
		s.send( MESSAGE )
		s.close()
	except Exception as e:
		print("Socket error!", e)

	print("\nWaiting for statistics\n")
	f = open("stats"+str(init)+".txt", "w")
	a = 1
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('192.168.1.230', PORT))
	s.listen(100)
	recvd_stats = {}
	while (a <= eds):
		(conn, addr) = s.accept()
		data = conn.recv(1024)
		if (len(data) > 10):
			try:
				(id, sf, deliv, retr, fail, rss, tx_t, rx_t, rwone, rwtwo) = struct.unpack('IBIIIfffii', data)
				if id not in recvd_stats:
					print(str(a)+".", hex(id), sf, deliv, retr, fail, rss, tx_t, rx_t, rwone, rwtwo)
					f.write( "%s: %s %s %s %s %s %s %s %s %s\n" % ( hex(id), str(sf), str(deliv), str(retr), str(fail), str(rss), str(tx_t), str(rx_t), str(rwone), str(rwtwo) ) )
					a += 1
					recvd_stats[id] = 1
			except Exception as e:
				print("wrong stat packet format!", e)
	f.close()
	s.close()
