#server.py
#Written by lyc 2015.12.31
#For Netease homework_2

import socket
import select
import pickle
import time
import threading
import random
import datetime


class csStat(object):
	def __init__(self, stat = 0, name = None):
		self.stat = stat
		self.name = name
		self.room = None
		self.logTime = 0
		self.game = 0

	def resetGame(self):
		self.game = 0

	def clear(self):
		self.stat = 0
		self.name = None
		self.room = None
		self.logTime = 0
		self.resetGame()

class roomStat(object):
	def __init__(self, numList =  [0,0,0,0], strnum = '0000'):
		self.numList = numList
		self.strnum = strnum
		self.winnerName = None
		self.winnerTime = 20
		self.winnerPoint = 0
		
	def clear(self):
		self.numList = [0,0,0,0]
		self.strnum = ''
		self.winnerName = None
		self.winnerTime = 20
		self.winnerPoint = 0

class pyChatServer(object):
	file = 'data.pkl'
	isGame = 0

	def gameOver(self):
		print '21 Game Over'
		self.isGame = 0
		self.gameBT = 0
		for r in self.roomdict:
			self.sendtoRoom(None, r, '21 Game Over')
			
			if self.roomdict[r].winnerName != None:
				tmp = 'Winner: %s Pt: %s Sec:%s'%(self.roomdict[r].winnerName, self.roomdict[r].winnerPoint, self.roomdict[r].winnerTime)
				self.sendtoRoom(None, r, tmp)
			else:
				self.sendtoRoom(None, r, 'No Winner')
			self.roomdict[r].clear()

		for each in self.cdict:
			self.cdict[each].resetGame()

	def randomNum(self):
		numnum = 4
		num = []
		s = ''
		for i in range(numnum):
			r = random.randint(1,10)
			s += '%s '% r
			num.append(r)
		return s, num

	def game(self, minute = -1):

		if self.isGame == 1:
			print 'Game already start.'
			return
		self.isGame = 1 
		if minute != -1:
			print 'Minute %s 21 Game Begin' % minute
		else:
			print '21 Game Begin'
		t = threading.Timer(15, self.gameOver,())
		for r in self.roomdict:
			snum, n = self.randomNum()
			self.roomdict[r] = roomStat(n, snum)
			
			self.gameBT = time.time()
			print '21Game Room %s %s'%(r, n)
			snum = '21 Game Begin: ' + snum
			self.sendtoRoom(None, r, snum)
		t.start()

		if minute != -1:
			self.countTime()

	def countTime(self, minute = 30):
		curMinute = datetime.datetime.now().minute
		curSecond = datetime.datetime.now().second

		deltaSec = 0

		if curMinute > minute or (curMinute == minute and curSecond != 0):
			deltaSec += (60 - curMinute + minute - 1) * 60
			deltaSec += 60 - curSecond
		elif curMinute < minute:
			deltaSec += (minute - curMinute - 1) *60
			deltaSec += 60 - curSecond

		t = threading.Timer(deltaSec, self.game,(minute,))
		t.start()

	def startGameByInput(self):
		
		self.countTime(self.min)
		while True:
			s = raw_input('>')
			if s.strip().lower() == 'game':
				self.game()

	def __init__(self, host, port, min = 30,lNum = 5):
		'''
		init server socket
		'''
		self.revBuf = 4096
		print 'Ip&port: ' + str(host) + ':' + str(port)
		self.ss = socket.socket()
		self.ss.bind((host, port))
		self.ss.listen(lNum)
		self.slist = [self.ss]

		self.cdict = {}

		self.isGame = 0
		self.gameBT = 0

		self.usrdict = {}
		self.roomdict = {}
		self.loadUsr()

		self.min = min
		
		print 'Run server...'
		self.runServer()

	def checkName(self, name):
		if name in self.usrdict:
			return True
		else:
			return False

	def checkPassword(self, name, password):
		if self.usrdict[name][0] == password:
			return True
		else:
			return False

	def storeUsr(self, file = file):
		f = open(file, 'wb')
		pickle.dump(self.usrdict, f)
		f.close()

	def loadUsr(self, file = file):
		try:
			f = open(file)
		except IOError:
			self.storeUsr()
			f = open(file)

		self.usrdict = pickle.load(f)
		f.close()

	def addName(self, name, password = 666):
		tmp = [password, 0]
		self.usrdict[name] = [tmp]
		self.storeUsr()
		
	def delName(self, name):
		del self.usrdict[name]
		self.storeUsr()

	def setPassword(self, name, password):
		self.usrdict[name][0] = password
		self.storeUsr()

	def cutTail(self, str):
		if str[-1] == '\n':
			return str[:-1]
		else:
			return str

	def sendFail(self, sock):
		if self.cdict[sock].stat == 10:
			self.offline(sock, self.cdict[sock].name)
		elif self.cdict[sock].stat in (2.1, 2.2):
			self.delName(self.cdict[sock].name)
			self.delcdict(sock)
		else:
			self.delcdict(sock)
		
	def send(self, sock, strData, sys = 0, roomNum = 0):
		if len(strData) == 0 or strData[-1] != '\n':
			strData += '\n'
		if sys == 0:
			strData = '[pub]' + strData
		elif sys == 1:
			 strData = '[sys]' + strData
		elif sys == 2:
			 strData = '[room ' + str(roomNum) + ']' + strData
		elif sys == 3:
			 strData = '[secret]' + strData
		try:			
			sock.send(strData)
		except:
			self.sendFail(sock)



	def sendAll(self, sock, strData, sys = 0):
		for cs in self.cdict:
			if cs != sock and self.cdict[cs].stat == 10:
				self.send(cs, strData, sys)

	def online(self, sock, name):
		print '%s is online' % name
		self.cdict[sock].logTime = time.time()
		self.sendAll(sock, '%s is online\n' % name, 1)
		self.send(sock, 'Welcome %s' % name, 1)

	def offline(self, sock, name):
		print '%s is offline' % name
		self.usrdict[name][1] += time.time() - self.cdict[sock].logTime
		self.storeUsr()
		self.sendAll(sock, '%s is offline\n' % name, 1)
		self.delcdict(sock)

	def delcdict(self, sock):
		del self.cdict[sock]

	def checkOnline(self, name):
		if len(name) == 0:
			return None
		for cs in self.cdict:
			if self.cdict[cs].name == name and self.cdict[cs].stat == 10:
				return cs
		return None

	
	def charge(self, sock, data):
		'''
		'''
		if sock not in self.cdict:
			print 'login sock is not in cdict'
			return

		if not data:
			return

		data = self.cutTail(data)

		if self.cdict[sock].stat == 0:
			if data == '1':
				self.send(sock, 'Please enter your name:', 1)
				self.cdict[sock].stat = 1
			elif data == '2':
				self.send(sock, 'Please enter your new name:', 1)
				self.cdict[sock].stat = 2
			else:
				self.send(sock, 'Please enter 1 or 2\n', 1)
				self.sendSign(sock)

		elif self.cdict[sock].stat == 1:
			if self.checkName(data):
				self.send(sock, 'Please enter your password:', 1)
				self.cdict[sock].name = data
				self.cdict[sock].stat = 1.5
			else:
				self.send(sock, 'Your name is NOT exsit\n', 1)
				self.send(sock, 'Please enter your name:', 1)
		elif self.cdict[sock].stat == 1.5:
			if self.checkPassword(self.cdict[sock].name, data):
				if self.checkOnline(self.cdict[sock].name):
					self.send(sock, '%s is already online\n' % self.cdict[sock].name, 1)
					self.sendSign(sock)
					self.cdict[sock].clear()
				else:
					self.cdict[sock].stat = 10
					self.online(sock, self.cdict[sock].name)
			else:
				self.send(sock, 'Your password is NOT right\n', 1)
				self.send(sock, 'Please enter your password:', 1)

		elif self.cdict[sock].stat == 2:
			if self.checkName(data):
				self.send(sock, 'Your name exsits\n', 1)
				self.send(sock, 'Please enter your new name:', 1)
			else:
				self.send(sock, 'Please enter your new password:', 1)
				self.cdict[sock].stat = 2.1
				self.cdict[sock].name = data
				self.addName(data)

		elif self.cdict[sock].stat == 2.1:
			self.setPassword(self.cdict[sock].name, data)
			self.cdict[sock].stat = 2.2
			self.send(sock, 'Please enter your new password again\n', 1)
		elif self.cdict[sock].stat == 2.2:
			if self.checkPassword(self.cdict[sock].name, data):
				self.send(sock, 'Signup success\n', 1)
				self.cdict[sock].stat = 10
				self.online(sock, self.cdict[sock].name)
			else:
				self.send(sock, 'Password is not same\n', 1)
				self.send(sock, 'Please enter your new password again\n', 1)

		elif self.cdict[sock].stat == 10:
			self.command(sock, data)

	def sendHelp(self, sock):
		whitespaceNum = 10
		tmp = 'Command:\n'
		tmp += '--all' + ' '*(whitespaceNum + 1) +'#send mesg to all\n'
		tmp += '--[name]' + ' '*(whitespaceNum -2) +'#send mesg to user [name]\n'
		tmp += '--time' + ' '*whitespaceNum +'#display your total online time\n'
		tmp += '--user' + ' '*whitespaceNum +'#display all online user\n'
		tmp += '--room' + ' '*whitespaceNum +'#display all room\n'
		tmp += '--room [num]' + ' '*(whitespaceNum - 6)+'#enter room [num], sample: --room 1\n'
		tmp += '--newroom [num]' + ' '*(whitespaceNum - 9)+'#create room num and then enter, sample: --newroom 1\n'
		tmp += '--exitroom' + ' '*(whitespaceNum - 4) +'#exit current room\n'
		self.send(sock, tmp, 1)

	def sendtime(self, sock, name):
		t = time.time()

		t = t - self.cdict[sock].logTime 
		t += self.usrdict[name][1]
		tmp = '%s Online Time: %fs'%(name, t)
		self.send(sock, tmp, 1)

	def getRoomDict(self):
		return self.roomdict

	def addRoom(self, num):
		self.roomdict[num] = roomStat()

	def sendroom(self, sock):

		room = self.getRoomDict()
		if len(room) == 0:
			tmp = 'No room'
		else:
			tmp = ''
			for each in room:
				tmp += '%s\t'%each
		self.send(sock, tmp, 1)

	def sendRequstHelp(self, sock):
		self.send(sock, 'Incorrent command\nInput \'--help\' for help\n', 1)

	def sendOnlineUsr(self, sock):
		tmp = ''
		for each in self.cdict:
			tmp += '--%s\t'%self.cdict[each].name
		self.send(sock, tmp, 1)

	

	def command(self, sock, data):
		data = data.strip()

		if data.startswith('--'):

			if data.lower() == '--help':
				self.sendHelp(sock)
			elif data.lower() == '--time':
				self.sendtime(sock, self.cdict[sock].name)
				
			elif data.lower() == '--room':
				self.sendroom(sock)
			elif data.lower() == '--user':
				self.sendOnlineUsr(sock)
			elif data.lower() == '--exitroom':
				if self.cdict[sock].room == None:
					self.send(sock, 'You are Not in room',1)
				else:
					self.send(sock, 'Exit room %s\n' % self.cdict[sock].room, 1)
					self.cdict[sock].room = None
			else:
				comm = data.split(None, 1)
				if comm[0].lower() == '--room':
					roomNum = None
					try:
						roomNum = int(comm[1])
					except:
						self.sendRequstHelp(sock)
						return
		
					if roomNum in self.getRoomDict():
						self.send(sock, 'Welcome to room %s\n' % roomNum, 1)
						self.cdict[sock].room = roomNum
					else:
						self.send(sock, 'No room %s\n' % roomNum, 1)
						
				elif comm[0].lower() == '--newroom':
					roomNum = None
					try:
						roomNum = int(comm[1])
					except:
						self.sendRequstHelp(sock)
						return

					if roomNum in self.getRoomDict():
						self.send(sock, 'Room %s exsits\n' % roomNum, 1)
						
					else:
						self.send(sock, 'Create room %s\n' % roomNum, 1)
						self.addRoom(roomNum)
						self.send(sock, 'Welcome to room %s\n' % roomNum, 1)
						self.cdict[sock].room = roomNum
				elif comm[0].lower() == '--all':
					data = comm[1]
					data = str(self.cdict[sock].name) + ':' + data			
					self.sendAll(sock, data, 0)
				elif comm[0].startswith('--'):
					iname = comm[0][2:]
					cs =  self.checkOnline(iname)
					if cs:
						data = str(self.cdict[sock].name) + ':' + comm[1]
						self.send(cs, data, 3)
					else:
						self.sendRequstHelp(sock)
				else:
					self.sendRequstHelp(sock)

		else:#not start with '--'
			
			room = self.cdict[sock].room 
			if room == None:
				data = str(self.cdict[sock].name) + ':' + data
				self.sendAll(sock, data, 0)
			else:
				gamecomm = '21game'
				if data.startswith(gamecomm) and self.isGame == 1:
					t = time.time() - self.gameBT
					if t > 15:
						self.send(sock, 'Time out',1)
					else:
						num = self.cal(data[len(gamecomm):], self.roomdict[room].strnum)
						
						if num == None:
							self.send(sock, 'Incorrent expression',1)
						else:
							if self.cdict[sock].game:
								self.send(sock, 'You have submitted', 1)
							else:
								print 'Room %s Name:%s Pt:%s Sec:%s'%(room, self.cdict[sock].name, num, t)
								self.cdict[sock].game = 1
								tmp = '%s Pt:%s Sec:%s'%(self.cdict[sock].name, num, t)
								self.send(sock, tmp, 1)
								if num <=21 and num >= self.roomdict[room].winnerPoint and t < self.roomdict[room].winnerTime:
									self.roomdict[room].winnerPoint = num
									self.roomdict[room].winnerTime = t
									self.roomdict[room].winnerName = self.cdict[sock].name
											
				else:
					data = str(self.cdict[sock].name) + ':' + data
					self.sendtoRoom(sock, room, data)
				
	def cal(self, s, strnum):
		mark = '+-*/()'
		space = ' \t\n'

		s = s.strip()
		for each in s:
			if each not in space and each not in mark:
				if each not in strnum:
					return None
				else:
					index = strnum.find(each)
					if index == -1:
						return None
					strnum = strnum[:index] + strnum[index+1:]
		try:
			return eval(s)
		except:
			return None

	def sendtoRoom(self, sock, roomNum, data, sys = 2):
		for cs in self.cdict:
			if cs != sock and self.cdict[cs].stat == 10 and self.cdict[cs].room == roomNum:
				self.send(cs, data, sys, roomNum)

	def sendSign(self,sock):
		self.send(sock, '1-signin\n[sys]2-signup\n', 1)

	def runServer(self):

		t = threading.Thread(target = self.startGameByInput)
		t.start()
		while True:				
			rs, ws, es = select.select(self.slist, [], [])
			
			for sock in rs:
				if sock == self.ss:#new connect to server
					newsock, addr = sock.accept()
					cstat = csStat()
					self.cdict[newsock] = cstat
					self.sendSign(newsock)
					self.slist.append(newsock)
					print 'New csock connect' + str(addr)
				else:
					try:
						revData = sock.recv(self.revBuf)
						if revData:
							self.charge(sock, revData)
   					except:
						self.sendFail(sock)
						sock.close()
						self.slist.remove(sock)
			

if __name__ == '__main__':
	s = pyChatServer(socket.gethostname(), 1234, 18)

