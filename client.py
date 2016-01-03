#client.py
#Written by lyc 2015.12.31
#For Netease homework_2

import socket
import telnetlib
import threading
import select

'''
class pyChatClient():

	def __init__(self, host, port):
		
		tn = telnetlib.Telnet(host, port)
		tn.mt_interact()
'''

class pyChatClient():
	def __init__(self, host, port):
		self.revBuf = 4096

		s = socket.socket()
		try:
			s.connect((host, port))
		except:
			print 'Unable to connect'
			return
		self.slist = [s]

		t = threading.Thread(target = self.input)
		t.start()
		self.run()

	def run(self):
		while True:
			try:
				rs, ws, es = select.select(self.slist, [], [])
			except:
				print 'connect failed'
				return
			for sock in rs:
				try:
					revData = sock.recv(self.revBuf)
					if revData:
						print revData,
				except:
					print 'connect failed'
					sock.close()
					return

	def input(self):
		while True:
			s = raw_input('>')
			for sock in self.slist:
				try:
					sock.send(s)
				except:
					print 'send failed'

if __name__ == '__main__':
	c = pyChatClient(socket.gethostname(), 1234)
