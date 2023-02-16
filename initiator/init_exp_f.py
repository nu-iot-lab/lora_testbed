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

PORT = 8000
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
		reboot_command = 'python3 webrepl/webrepl_client.py -p 97079088 192.168.1.40 < <(echo -e "import machine" && echo -e "machine.reset()" && echo -e "exit")'
		if (items[0] == 'GW'):
			# launch send script with args for the GW

			#src_file = "SOURCE_FILE_NAME"
			#remote_path = IP + ":/" + "REMOTE_FILE_NAME"

			src_file = "cool.txt"
			remote_path = IP + ":/" + "remote_cool.txt"

			#print("#############################")
			#print("Uploading to GW {path}".format(path = remote_path))
			#print("#############################")
			cmd = ['python3', 'webrepl/webrepl_cli.py', '-p', passwd, src_file, remote_path]
			p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
			for line in p.stdout:
				print(line.decode("utf-8"))
			p.wait()
			print(" ######### REBOOT INITIATED  ###########   ")
			reboot_process = subprocess.Popen(reboot_command ,shell = True, stdout = subprocess.PIPE, executable='/bin/bash')
			time.sleep(3)
			reboot_process.kill()
			print(" ######### REBOOT FINISHED  ###########   ")
		elif (items[0] == 'ED'):
			# launch send script with args for the GW

			#src_file = "SOURCE_FILE_NAME"
			#remote_path = IP + ":/" + "REMOTE_FILE_NAME"

			src_file = "cool.txt"
			remote_path = IP + ":/" + "remote_cool.txt"

			#print("#############################")
			#print("Uploading to GW {path}".format(path = remote_path))
			#print("#############################")
			cmd = ['python3', 'webrepl/webrepl_cli.py', '-p', passwd, src_file, remote_path]
			p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
			for line in p.stdout:
				print(line.decode("utf-8"))
			p.wait()
			print(" ######### REBOOT INITIATED  ###########   ")
			reboot_process = subprocess.Popen(reboot_command ,shell = True, stdout = subprocess.PIPE, executable='/bin/bash')
			time.sleep(3)
			reboot_process.kill()
			print(" ######### REBOOT FINISHED  ###########   ")
		else:
			continue
elif mode == 'C':
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
