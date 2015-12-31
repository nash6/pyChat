#server.py
#Written by lyc 2015.12.31
#For Netease homework_2

import socket
import select


class pyChatServer():

	def __init__(self, host, port, lNum = 5):
		'''init server socket
		'''
		revBuf = 4096

		print 'Ip&port: ' + str(host) + ':' + str(port)
		self.ss = socket.socket()
		self.ss.bind((host, port))
		self.ss.listen(lNum)
		self.slist = [self.ss]
		
		print 'Run server...'
		self.runServer()
		
	def runServer(self):
		while True:
			rs, ws, es = select.select(self.slist, [], [])
			for sock in rs:
				if sock == self.ss:#new connect to server
					newsock, addr = sock.accept()
					self.slist.append(newsock)
					print 'New sock ' + str(addr)
				else:
					try:
						revData = sock.recv(revBuf)
						if revData:
							boardcastMess(sock, str(sock.getpeername()) +': ' + str(revData) + '\n')
					except:
						print 'recv fail' + str(sock) 
						sock.close()
						self.slist.remove(sock)

	def boardcastMess(self, srcSock, strMess):
		for sock in self.slist:
			if sock != self.ss and sock != srcSock:
				try:
					sock.send(strMess)
				except:
					print 'sent fail' + str(sock) 
					sock.close()
					self.slist.remove(sock)



if __name__ == '__main__':
	s = pyChatServer(socket.gethostname(), 1234)

