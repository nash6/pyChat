#client.py
#Written by lyc 2015.12.31
#For Netease homework_2

import socket
import getpass
import telnetlib


class pyChatClient():

	def __init__(self, host, port):
		'''
		'''
		tn = telnetlib.Telnet(host, port)
		tn.mt_interact()
	


if __name__ == '__main__':
	c = pyChatClient(socket.gethostname(), 1234)

