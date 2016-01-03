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
		'''client socket status class
		'''
		self.stat = stat
		'''
		status include:
		0 #signin or signup
		1 #signin enter name
		1.5 #signin enter password
		2 #signup enter name
		2.1 #signup enter password
		2.2 #signup enter password again
		10 #login success
		'''
		self.name = name #your user name
		self.room = None #the room you are in
		self.logTime = 0 #the online time(sec) since you login this time
		self.game = 0 #you have submit a corrent game answer or not

	def resetGame(self):
		'''reset game flag every game round
		'''
		self.game = 0

	def clear(self):
		'''reset all
		'''
		self.stat = 0
		self.name = None
		self.room = None
		self.logTime = 0
		self.resetGame()

class roomStat(object):
	def __init__(self, numList =  [0,0,0,0], strnum = '0000'):
		'''room status class
		'''
		self.numList = numList #the game number list
		self.strnum = strnum #the string of game number list
		self.winnerName = None #winner name
		self.winnerTime = 20 #winner's submit time(sec)
		self.winnerPoint = 0 #winner's point
		
	def clear(self):
		'''reset all
		'''
		self.numList = [0,0,0,0]
		self.strnum = '0000'
		self.winnerName = None
		self.winnerTime = 20
		self.winnerPoint = 0

class pyChatServer(object):
	
	file = 'data.pkl' #local file name for (name, password, online time)
	isGame = 0 #the game is on or not

	def gameOver(self):
		'''should be called when game time counting is over
		'''
		print '21 Game Over'
		self.isGame = 0
		self.gameBT = 0 #reset game begin time

		for r in self.roomdict:
			self.sendtoRoom(None, r, '21Game Over') #send game over to every room
			
			if self.roomdict[r].winnerName != None: #send winner name
				tmp = 'Winner: %s Pt: %s Sec:%s'%(self.roomdict[r].winnerName, self.roomdict[r].winnerPoint, self.roomdict[r].winnerTime)
				self.sendtoRoom(None, r, tmp)
			else:
				self.sendtoRoom(None, r, 'No Winner')

			self.roomdict[r].clear() #clear room status

		for each in self.cdict:
			self.cdict[each].resetGame() #clear user's submit flag

	def randomNum(self):
		'''generate 4 random integer numbers in range 1-10
		return (numstr, numlist)
		'''
		numnum = 4
		num = []
		s = ''
		for i in range(numnum):
			r = random.randint(1,10)
			s += '%s '% r
			num.append(r)
		return s, num

	def game(self, minute = -1):
		'''should be called when game begin
		argu minute indicate the minute when game is on. if -1 when start game by command 
		'''
		gameDurTime = 15 #game last for 15 second

		if self.isGame == 1:# is game already on?
			print '21Game already start.'
			return

		self.isGame = 1 #game flag on

		print '21Game will start in 3s'
		for r in self.roomdict: 
			self.sendtoRoom(None, r, '21Game will start in 3s')
		time.sleep(1)

		print '21Game will start in 2s'
		for r in self.roomdict: 
			self.sendtoRoom(None, r, '21Game will start in 2s')
		time.sleep(1)

		print '21Game will start in 1s'
		for r in self.roomdict: 
			self.sendtoRoom(None, r, '21Game will start in 1s')
		time.sleep(1)

		if minute != -1: #time out
			print 'M%s 21 Game Begin' % minute
		else: #command start game
			print '21Game Begin'

		t = threading.Timer(gameDurTime, self.gameOver,()) #set timer 

		for r in self.roomdict: #game question dilvered
			snum, n = self.randomNum()
			self.roomdict[r] = roomStat(n, snum)
			
			self.gameBT = time.time()
			print '21Game Room %s: %s'%(r, n)

			snum = '21 Game Begin: ' + snum
			self.sendtoRoom(None, r, snum)

		t.start()

		if minute != -1: #if this game start by timing out
			self.countTime() #set timer for next round game

	def countTime(self, minute = 30):
		'''start timer for game
		argu minute indicate the minute to begin game every hour
		'''
		curTime = datetime.datetime.now() #get current time
		curMinute = curTime.minute 
		curSecond = curTime.second

		deltaSec = 0 #delta second till next game

		if curMinute > minute or (curMinute == minute and curSecond != 0): #wait >= minute
			deltaSec += (60 - curMinute + minute - 1) * 60
			deltaSec += 60 - curSecond
		elif curMinute < minute: #wait < minute
			deltaSec += (minute - curMinute - 1) *60
			deltaSec += 60 - curSecond

		t = threading.Timer(deltaSec, self.game,(minute,)) #set timer
		t.start()

	def startGameByInput(self):
		'''game thread func
		'''
		self.countTime(self.min) #set timer for game

		#also can call game on by command
		while True:
			s = raw_input('>') 
			if s.strip().lower() == 'game':
				self.game()

	def __init__(self, host, port, min = 30,lNum = 5):
		'''chat server class
		agru host:port, min for game start minute every hour, listen num
		'''

		self.revBuf = 4096 #socket recv(size)

		print 'Host & port: ' + str(host) + ':' + str(port)

		#init server socket
		self.ss = socket.socket()
		try:
			self.ss.bind((host, port))
		except:
			print 'bind error'
			return
		self.ss.listen(lNum)
		self.slist = [self.ss]

		self.cdict = {} #client socket: cs status

		self.isGame = 0 #reset game flag
		self.gameBT = 0 #reset game begin time

		self.usrdict = {} #user name and [password, logtime]
		self.roomdict = {} #room number: room status

		self.loadUsr() #load user info from file

		self.min = min #game start minute every hour
		
		print 'Server Run...'
		self.runServer()

	def checkName(self, name):
		'''check name is registered or not
		'''
		if name in self.usrdict:
			return True
		else:
			return False

	def checkPassword(self, name, password):
		'''check password is right or not
		'''
		if self.usrdict[name][0] == password: #user name : [password, logtime]
			return True
		else:
			return False

	def storeUsr(self):
		'''dump user info to file
		'''
		f = open(self.file, 'wb')
		pickle.dump(self.usrdict, f)
		f.close()

	def loadUsr(self):
		'''load user info from file
		'''
		try:
			f = open(self.file)
		except IOError:
			self.storeUsr()
			f = open(self.file)

		self.usrdict = pickle.load(f)
		f.close()

	def addName(self, name, password = 1234):
		'''add a user name to memory and disk
		'''
		tmp = [password, 0]
		self.usrdict[name] = tmp
		self.storeUsr()
		
	def delName(self, name):
		'''del a user name to memory and disk
		'''
		del self.usrdict[name]
		self.storeUsr()

	def setPassword(self, name, password):
		'''set password to memory and disk
		'''
		self.usrdict[name][0] = password
		self.storeUsr()

	def cutTail(self, str):
		'''cut recv string tail '\n'
		'''
		if str[-1] == '\n':
			return str[:-1]
		else:
			return str

	def sendFail(self, sock):
		'''called when client socket disconnected or error
		'''
		if self.cdict[sock].stat == 10:
			self.offline(sock) #offline func
		elif self.cdict[sock].stat in (2.1, 2.2): #disconnect when enter password for signup 
			self.delName(self.cdict[sock].name)
			self.delcdict(sock)
		else:
			self.delcdict(sock)
		
	def send(self, sock, strData, sys = 0, roomNum = 0):
		'''send mesg to client
		argu sock: cssock, strData: send data, sys: mesg source, roomNum: send in roomdict
			sys:
			0 pub 
			1 sys
			2 room
			3 secret #send to someone only
		'''
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
		'''send to every user online
		'''
		for cs in self.cdict:
			if cs != sock and self.cdict[cs].stat == 10:
				self.send(cs, strData, sys)

	def online(self, sock, name):
		'''called when user online
		'''
		print '%s is online' % name
		self.cdict[sock].logTime = time.time()
		self.sendAll(sock, '%s is online\n' % name, 1)
		self.send(sock, 'Welcome %s' % name, 1)

	def offline(self, sock):
		'''calledn when user offline
		'''
		name = self.cdict[sock].name
		print '%s is offline' % name

		self.usrdict[name][1] += time.time() - self.cdict[sock].logTime
		self.storeUsr()

		self.sendAll(sock, '%s is offline\n' % name, 1)
		self.delcdict(sock)

	def delcdict(self, sock):
		del self.cdict[sock]

	def checkOnline(self, name):
		'''check user is online or not
		return the user's client socket or None
		'''
		if len(name) == 0:
			return None
		for cs in self.cdict:
			if self.cdict[cs].name == name and self.cdict[cs].stat == 10:
				return cs
		return None

	def charge(self, sock, data):
		'''handle the user input
		'''
		if sock not in self.cdict:
			print 'login sock is not in cdict'
			return

		if not data:
			return

		data = self.cutTail(data)

		'''
		status change

		0---->1---->1.5--------->10
		|						  |
		|---->2---->2.1<--->2.2-->|
		'''

		if self.cdict[sock].stat == 0:
			if data == '1': #signin
				self.send(sock, 'Please enter your name:', 1)
				self.cdict[sock].stat = 1
			elif data == '2': #signup
				self.send(sock, 'Please enter your new name:', 1)
				self.cdict[sock].stat = 2
			else:
				self.send(sock, 'Please enter 1 or 2\n', 1)
				self.sendSign(sock)

		elif self.cdict[sock].stat == 1: #signin
			if self.checkName(data): #name exsit
				self.send(sock, 'Please enter your password:', 1)
				self.cdict[sock].name = data
				self.cdict[sock].stat = 1.5
			else: #name not exsit
				self.send(sock, 'Your name do NOT exsit\n', 1)
				self.cdict[sock].clear()
				self.sendSign(sock)

		elif self.cdict[sock].stat == 1.5: #enter password
			if self.checkPassword(self.cdict[sock].name, data): #ps right
				if self.checkOnline(self.cdict[sock].name): #already online
					self.send(sock, '%s is already online\n' % self.cdict[sock].name, 1)
					self.cdict[sock].clear()
					self.sendSign(sock)				
				else:
					self.cdict[sock].stat = 10
					self.online(sock, self.cdict[sock].name)
			else: #ps wrong
				self.send(sock, 'Your password is NOT right\n', 1)
				self.cdict[sock].clear()
				self.sendSign(sock)
				
		elif self.cdict[sock].stat == 2: #signup
			if self.checkName(data): #name exsits
				self.send(sock, 'Your name exsits\n', 1)
				self.cdict[sock].clear()
				self.sendSign(sock)
			else: #name not comflict
				self.send(sock, 'Please enter your new password:', 1)
				self.cdict[sock].stat = 2.1
				self.cdict[sock].name = data
				self.addName(data)

		elif self.cdict[sock].stat == 2.1: #new password 1st
			self.setPassword(self.cdict[sock].name, data)
			self.cdict[sock].stat = 2.2
			self.send(sock, 'Please enter your new password again\n', 1)

		elif self.cdict[sock].stat == 2.2: #new password 2nd
			if self.checkPassword(self.cdict[sock].name, data):
				self.send(sock, 'Signup success\n', 1)
				self.cdict[sock].stat = 10
				self.online(sock, self.cdict[sock].name)
			else: #password is NOT the same
				self.send(sock, 'Password is not same\n', 1)
				self.send(sock, 'Please enter your new password again\n', 1)

		elif self.cdict[sock].stat == 10: #online
			self.command(sock, data)

	def sendHelp(self, sock):
		'''send command info to client
		'''
		whitespaceNum = 10
		tmp = 'Command List:\n'
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
		'''send total online time(sec) to client
		'''
		t = time.time()

		t = t - self.cdict[sock].logTime 
		a = t + self.usrdict[name][1]
		tmp = '%s\'s Online Time: %.2fs'%(name, t)
		tmp += '\n'
		tmp += '[sys]%s\'s Total Online Time: %.2fs'%(name, a)
		self.send(sock, tmp, 1)

	def getRoomDict(self):
		return self.roomdict

	def addRoom(self, num):
		'''create new room
		'''
		self.roomdict[num] = roomStat()

	def sendroom(self, sock):
		'''send all current room num to client 
		'''
		room = self.getRoomDict()
		if len(room) == 0:
			tmp = 'No room'
		else:
			tmp = ''
			for each in room:
				tmp += '%s '%each
		self.send(sock, tmp, 1)

	def sendRequstHelp(self, sock):
		self.send(sock, 'Incorrent command\nInput \'--help\' for help\n', 1)

	def sendOnlineUsr(self, sock):
		'''send online user list to client
		'''
		tmp = ''
		for each in self.cdict:
			tmp += '--%s '%self.cdict[each].name
		self.send(sock, tmp, 1)

	def command(self, sock, data):
		'''online user's command parser func
		'''
		data = data.strip() #cut head and tail

		if data.startswith('--'): #command --
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
					self.send(sock, 'You are Not in any room',1)
				else:
					self.cdict[sock].room = None
					self.send(sock, 'Exit room %s\n' % self.cdict[sock].room, 1)					
			else:
				comm = data.split(None, 1) #cut data into 2 slices
				if comm[0].lower() == '--room':
					roomNum = 0

					try:
						roomNum = int(comm[1])
					except:
						self.sendRequstHelp(sock) #incorrent command
						return
		
					if roomNum in self.getRoomDict():
						self.cdict[sock].room = roomNum
						self.send(sock, 'Welcome to room %s\n' % roomNum, 1)					
					else:
						self.send(sock, 'There is no room %s\nTry input --room to check all room number\n' % roomNum, 1)
						
				elif comm[0].lower() == '--newroom': #create room
					roomNum = 0
					try:
						roomNum = int(comm[1])
					except:
						self.sendRequstHelp(sock)
						return

					if roomNum in self.getRoomDict(): #room exsits
						self.send(sock, 'Room %s exsits\n' % roomNum, 1)
						
					else:
						self.addRoom(roomNum)
						self.send(sock, 'Create room %s\n' % roomNum, 1)
						self.cdict[sock].room = roomNum
						self.send(sock, 'Welcome to room %s\n' % roomNum, 1)
						
				elif comm[0].lower() == '--all': #send mesg to all
					data = comm[1]
					data = str(self.cdict[sock].name) + ':' + data			
					self.sendAll(sock, data, 0)
				elif comm[0].startswith('--'): #secret chat
					iname = comm[0][len('--'):]
					cs = self.checkOnline(iname)
					if cs:
						data = str(self.cdict[sock].name) + ':' + comm[1]
						self.send(cs, data, 3)
					else:
						self.send(sock, 'No such user or user is not online\nTry input --user to check online user name\n', 1)
				else:
					self.sendRequstHelp(sock)

		else:#not start with '--'		
			room = self.cdict[sock].room 
			if room == None: #send to all
				data = str(self.cdict[sock].name) + ':' + data
				self.sendAll(sock, data, 0)
			else:
				gamecomm = '21game'
				if data.lower().startswith(gamecomm) and self.isGame == 1: #game time
					t = time.time() - self.gameBT
					if t > 15:
						self.send(sock, 'Game time out',1)
					else:
						num = self.cal(data[len(gamecomm):], self.roomdict[room].strnum)
						
						if num == None:
							self.send(sock, 'Incorrent expression',1)
						else:
							if self.cdict[sock].game:
								self.send(sock, 'You have submitted', 1)
							else:
								print 'Game Room %s Name:%s Pt:%s Sec:%s'%(room, self.cdict[sock].name, num, t)
								self.cdict[sock].game = 1
								tmp = '%s Pt:%s Sec:%s'%(self.cdict[sock].name, num, t)
								self.send(sock, tmp, 1)
								if num <=21:
									if num > self.roomdict[room].winnerPoint or (num == self.roomdict[room].winnerPoint and t < self.roomdict[room].winnerTime):
										self.roomdict[room].winnerPoint = num
										self.roomdict[room].winnerTime = t
										self.roomdict[room].winnerName = self.cdict[sock].name
											
				else: #normal mesg in room
					data = str(self.cdict[sock].name) + ':' + data
					self.sendtoRoom(sock, room, data)
				
	def cal(self, s, strnum):
		'''cal the expression
		return number or None if illegal expression
		'''
		mark = '+-*/()'
		space = ' \t\n'

		s = s.strip()
		#check expression's element is legal or not
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
		'''send mesg to others in the same room
		'''
		for cs in self.cdict:
			if cs != sock and self.cdict[cs].stat == 10 and self.cdict[cs].room == roomNum:
				self.send(cs, data, sys, roomNum)

	def sendSign(self,sock):
		self.send(sock, ' Input 1 or 2 for:\n[sys] 1 - Sign In\n[sys] 2 - Sign Up\n', 1)

	def runServer(self):
		'''run server
		'''
		#game thread
		t = threading.Thread(target = self.startGameByInput)
		t.start()

		while True:				
			rs, ws, es = select.select(self.slist, [], [])
			
			for sock in rs:
				if sock == self.ss: #new connect to server
					newsock, addr = sock.accept()

					cstat = csStat()
					self.cdict[newsock] = cstat
					self.sendSign(newsock)

					self.slist.append(newsock)
					print 'New client socket connect' + str(addr)
				else:
					try:
						revData = sock.recv(self.revBuf)
						if revData:
							self.charge(sock, revData) #handle revdata
   					except:
						self.sendFail(sock)
						sock.close()
						self.slist.remove(sock)
			

if __name__ == '__main__':
	gameTriggerMinute = 30
	host = socket.gethostname()
	port = 1234
	s = pyChatServer(host, port, gameTriggerMinute)

