import datetime
import struct
import logging
logger = logging.getLogger()
logger.info("*** imported RFM69 mock ***")

'''
For reference when making dummy data
config["ENV_DATA_LENGTH"] = 13
config["MSG_NUMBER_BYTE"] = 1
config["TEMPV_BYTE_MSB"] = 2
config["TEMPV_BYTE_LSB"] = 3
config["TEMPO_BYTE_MSB"] = 4
config["TEMPO_BYTE_LSB"] = 5
config["HUMIDITYV_BYTE"] = 6
config["HUMIDITYO_BYTE"] = 7
config["VOLTAGE_BYTE_MSB"] = 8
config["VOLTAGE_BYTE_LSB"] = 9
config["VENT_BYTE"] = 10
config["HUMIDITYAV_BYTE"] = 11
config["VER_BYTE_MSB"] = 12
config["VER_BYTE_LSB"] = 13
'''

class RFM69(object):
	def __init__(self, freqBand, nodeID, networkID, isRFM69HW = False, intPin = 18, rstPin = 29, spiBus = 0, spiDevice = 0):
		self.freqBand = freqBand
		self.address = nodeID
		self.networkID = networkID
		self.isRFM69HW = isRFM69HW
		self.intPin = intPin
		self.rstPin = rstPin
		self.spiBus = spiBus
		self.spiDevice = spiDevice
		self.intLock = False
		self.mode = ""
		self.promiscuousMode = False
		self.DATASENT = False
		self.DATALEN = 0
		self.SENDERID = 99
		self.TARGETID = 0
		self.PAYLOADLEN = 0
		self.ACK_REQUESTED = 0
		self.ACK_RECEIVED = 0
		self.RSSI = -30
		
		# some dummy data to send back on receive
		tempv = 21 * 100
		tempo = 21 * 100
		humidv = 50 * 2
		humido = 50 * 2
		voltage = 3.5 * 5000
		vent = 0
		hAv = 50 * 2
		ver = 3015
		self._lastSecond = 0
		# Includes one pad and one message number
		self.DATA = struct.pack(">BBhhBBhBBh", 0, 0, tempv, tempo, humidv, humido, voltage, vent, hAv, ver)
		self.sendSleepTime = 0.01
	
	def setFreqeuncy(self, FRF):
		pass

	def setMode(self, newMode):
		pass
	
	def sleep(self):
		pass

	def setAddress(self, addr):
		pass

	def setNetwork(self, networkID):
		pass

	def setPowerLevel(self, powerLevel):
		pass

	def canSend(self):
		return True

	def send(self, toAddress, buff = "", requestACK = False):
		logger.info("Sending {} to {}".format(buff, toAddress))

	def sendWithRetry(self, toAddress, buff = "", retries = 3, retryWaitTime = 10):
		return False

	def ACKReceived(self, fromNodeID):
		return False

	def ACKRequested(self):
		return True

	def sendACK(self, toAddress = 0, buff = ""):
		pass
		
	def sendFrame(self, toAddress, buff, requestACK, sendACK):
		pass

	def interruptHandler(self, pin):
		pass

	def receiveBegin(self):
		pass

	def receiveDone(self):
		'''
		Return True every n seconds to simulate periodic data
		'''
		curSecond = datetime.datetime.utcnow().second
		if curSecond % 2 == 0 and curSecond != self._lastSecond:
			self._lastSecond = curSecond
			return True
		else:
			return False

	def readRSSI(self, forceTrigger = False):
		return self.RSSI

	def encrypt(self, key):
		pass

	def readReg(self, addr):
		return 0

	def writeReg(self, addr, value):
		pass
	
	def promiscuous(self, onOff):
		pass
	
	def setHighPower(self, onOff):
		pass
		
	def setHighPowerRegs(self, onOff):
		pass

	def readAllRegs(self):
		return []

	def readTemperature(self, calFactor):
		return 21

	def rcCalibration(self):
		pass

	def shutdown(self):
		pass