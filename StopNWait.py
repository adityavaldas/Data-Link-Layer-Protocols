from threading import Thread
import numpy as np
import logging
import os
import sys
import subprocess
import time
from random import randint

class StopNWait():
	def __init__(self):

		'''Change this to change probability of 1 bit erroring out in channel transmission'''
		self.ErrorProb = 30
		'''Change this to set framelength in "bits" '''
		self.FrameLength = 64
		'''Set percentage of failure rate of receiver ack reaching transmitter'''
		self.RxAckFailProb = 10
		'''Set timeout for transmitter when waiting for receiver ACK'''
		self.TxWaitTime = 5
		'''Set duration of running the simulation test'''
		self.runDuration = 60
		'''Change this to change the polynomial to calculate CRC'''
		self.CrcPoly = '1011'
		self.TransmissionTime = 1
		self.TxBufNo = '0'
		# self.RxBufNo = '0'
		self.TxPacket = ''
		self.TxBuffer = ''
		self.RxBuffer = ''
		self.ChannelTxBuffer = ''
		self.ChannelRxBuffer = ''
		self.FrameData = ''
		self.CrcData = ''
		self.CrcLength = len(self.CrcPoly)-1
		self.ActionBy = 0

	def Run(self):
		self.t1 = time.time()
		self.startTxThread()
		self.startRxThread()

	def startTxThread(self):
		log.info('TX -> Sending first packet')
		self.setTxPacket()
		self.sendTxPacket()
		# log.debug('Setting ActionBy to 1 (1st time)')
		self.ActionBy = 1
		# log.debug('Starting TX Thread')
		Thread(target = self.TxFunction, args = ()).start()

	def startRxThread(self):
		# log.debug('Starting RX Thread')
		Thread(target = self.RxFunction, args = ()).start()

	def TxFunction(self):
		while(time.time()-self.t1<self.runDuration):
			# log.debug('In TX Thread')
			if(self.ActionBy == 0):
				print()
				time.sleep(self.TransmissionTime)
				# log.debug('In TX Function')
				for i in range(self.TxWaitTime):
					if(self.RxBufNo == ''):
						log.error('TX -> Did not receive ACK at all from RX, waiting')
						time.sleep(1)
					else:
						break
				if(self.RxBufNo == ''):
					log.error('TX -> Did not receive ACK at all from RX for packet {}, resending the packet'.format(self.TxBufNo))
					self.sendTxPacket()
				elif(self.TxBufNo == self.RxBufNo):
					log.error('TX -> Did not receive proper ACK from RX for packet {}, resending the packet'.format(self.TxBufNo))
					self.sendTxPacket()
				else:
					pr = self.TxBufNo
					self.TxBufNo = self.RxBufNo
					log.info('TX -> Received proper ACK from RX for packet {}, sending packet {}'.format(pr, self.TxBufNo))
					self.setTxPacket()
					self.sendTxPacket()
				# log.debug('Setting ActionBy to 1')
				self.ActionBy = 1

	def sendTxPacket(self):
		self.ChannelTxBuffer = self.AddNoise(self.TxPacket)
		# log.debug('After channel no: {}'.format(self.ChannelTxBuffer))

	def AddNoise(self, strr):
		r = randint(0,10)
		er = self.ErrorProb/10
		if(r<=er):
			log.error('CHANNEL -> Channel corrupted transmitted message')
			if(strr[2] == '1'):
				strr1 = strr[:2] + '0' + strr[3:]
			else:
				strr1 = strr[:2] + '1' + strr[3:]
			return strr1
		else:
			log.info('CHANNEL -> No corruption through channel')
		return strr


	def setTxPacket(self):
		self.FrameData = self.genRandomFrame()
		self.CrcData = self.genCrcData(self.FrameData)
		# log.debug('self.FrameData: {}'.format(self.FrameData))
		# log.debug('self.CrcData: {}'.format(self.CrcData))
		self.TxPacket = self.TxBufNo + self.FrameData + self.CrcData
		# log.debug('Set Tx Packet to: {}'.format(self.TxPacket))

	def genRandomFrame(self):
		strr = ''
		for i in range(self.FrameLength):
			strr = strr + str(randint(0,1))
		# log.debug('add: {}'.format(strr))
		return strr

	def genCrcData(self, frame):
		strr = ''
		for i in range(self.CrcLength):
			strr = strr + '0'
		add = frame + strr
		# log.debug('add: {}'.format(add))
		while('1' in add[:self.FrameLength]):
			for i in range(len(add)):
				if(add[i]=='1'):
					start = i
					break
			sub = self.genSub(add, start)
			add = self.xorr(add, sub)
			# log.debug('xor: {}'.format(add))
		# log.debug('crc calculated: {}'.format(add[-3:]))
		return(add[-3:])


	def genSub(self, add, start):
		strr = ''
		for i in range(start):
			strr = strr + '0'
		strr = strr + self.CrcPoly
		for i in range(len(add) - start - self.CrcLength - 1):
			strr = strr + '0'
		# log.debug('Sub: {}'.format(strr))
		return strr

	def xorr(self, a, b):
		if(len(a)!=len(b)):
			log.debug('Requested to XOR strings of unequal length')
			exit()
		result = ''
		for i in range(len(a)):
			if(a[i] == b[i]):
				result = result + '0'
			else:
				result = result + '1'
		# log.debug('Result of XOR: {}'.format(result))
		return result

	def RxFunction(self):

		# log.debug('In RX Thread')
		while(time.time()-self.t1<self.runDuration):
			# log.debug('ActionBy: {}'.format(self.ActionBy))
			if(self.ActionBy == 1):
				time.sleep(self.TransmissionTime)
				# log.debug('In RX Function')
				# log.debug('Calculating CRC for: {}'.format(self.ChannelTxBuffer[1:-self.CrcLength]))
				crc = self.genCrcData(self.ChannelTxBuffer[1:-self.CrcLength])
				# log.info('CRC at receiver: {}'.format(crc))
				if(crc == self.ChannelTxBuffer[-3:]):
					log.info('RX -> CRC matched. Verified message at receiver side')
					pr = self.TxBufNo
					if(self.TxBufNo == '1'):
						self.RxBufNo = '0'
					else:
						self.RxBufNo = '1'
					log.info('RX -> Received packet {}, requesting for packet {}'.format(pr, self.RxBufNo))
				else:
					log.error('RX -> CRC does not match. Could not verify message at receiver side')
					self.RxBufNo = self.TxBufNo
					log.info('RX -> Requesting resend of packet {}'.format(self.TxBufNo))

				log.debug('Setting ActionBy to 0')
				g = randint(1,100)
				if(g<self.RxAckFailProb):
					log.error('CHANNEL -> ACK from RX did not reach transmitter')
					self.RxBufNo = ''
				self.ActionBy = 0


'''
MAIN FUNCTION
'''

log = logging.getLogger('simple_example')
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
if('--d' in sys.argv):
	log = logging.getLogger('simple_example')
	log.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)6s: %(message)s','%d-%b-%y %H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)
os.system('cls')

sw = StopNWait()
sw.Run()
