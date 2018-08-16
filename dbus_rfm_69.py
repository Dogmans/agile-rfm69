#!/usr/bin/env python2
# --- Imports -----------
import logging
import struct
import time

from twisted.internet import reactor, defer
from txdbus import client, objects, error
from txdbus.interface import DBusInterface, Method

from config import *
from RFM69 import RFM69
from RFM69.RFM69registers import *
	
class Rfm69DBusService(objects.DBusObject):
	
	class NotImplementedError(Exception):
		dbusErrorName = "org.agile-rfm69.NotImplemented"
	
	class IOError(Exception):
		dbusErrorName = "org.agile-rfm69.IOError"
	
	class ValueError(Exception):
		dbusErrorName = "org.agile-rfm69.ValueError"
	
	class TypeError(Exception):
		dbusErrorName = "org.agile-rfm69.TypeError"
	
	iface = DBusInterface("iot.agile.Protocol",
					Method("Connect"),
					Method("Connected", returns="b"),
					Method("Disconnect"),
					Method("Setup", arguments="a{sv}"),
					Method("Send", arguments="a{sv}"),
					Method("Receive", returns="a{sv}"),
					Method("Name", returns="s"),
					Method("Driver", returns="s"),
					Method("Discover", returns="a{sv}"),
					Method("Exec", arguments="a{sv}"),
					Method("Subscribe", arguments="a{sv}")
					)
	
	dbusInterfaces = [iface]
	
	def __init__(self, objectPath):
		super(Rfm69DBusService, self).__init__(objectPath)
		self._logger = logging.getLogger()
		self._full_path = PROTOCOL_PATH
		self._connected = False
		self._setup = {
			"MODEM_CONFIG_TABLE": MODEM_CONFIG_TABLE,
			"MODEM_CONFIG": MODEM_CONFIG,
			"key": MODEM_KEY,
			"channel": CHANNEL
		}

	def _setModemConfig(self):
		# Set RFM69 registers as per config
		settings = MODEM_CONFIG_TABLE[self._setup["MODEM_CONFIG"]]
		addresses = [0x02, 0x03, 0x04, 0x05, 0x06, 0x19, 0x1a, 0x37]
		for value, address in zip(settings, addresses):
			self._rfm69.writeReg(address, value)
			
	def _setModemKey(self):
		self._logger.debug("enabling ecryption")
		self._rfm69.encrypt(self._setup["key"])
		
	def _getConnected(self):
		return self._connected
	
	def _setConnected(self, status):
		if status:
			self._connected = True
		else:
			self._connected = False 
	
	def dbus_Connect(self):
		self._logger.debug(
			"{}@Connect: Connect INIT".format(self._full_path))
		if self._getConnected():
			self._logger.debug(
				"{}@Connect: Module is already connected".format(self._full_path))
			raise self.IOError("Module is already connected.")
		
		self._logger.debug(
			"{}@Connect: MODE={}".format(self._full_path, self._setup["MODEM_CONFIG"]))
		self._rfm69 = RFM69.RFM69(RF69_868MHZ, 1, self._setup["channel"], True, 18, 22) # TODO - make configurable if continuing with this interface
		
		self._logger.debug("class initialized")
		self._logger.debug("Performing rcCalibration")
		self._rfm69.rcCalibration()
		self._logger.debug("setting high power")
		self._rfm69.setHighPower(True)
		self._logger.debug("Checking temperature")
		self._logger.debug(self._rfm69.readTemperature(0))
		
		# Make sure settings are correct to talk to other radios
		self._setModemConfig()
		self._setModemKey()
		
		self._logger.debug("reading all registers")
		results = self._rfm69.readAllRegs()
		for result in results:
			self._logger.debug(result)
		
		# Won't get here if something went wrong reading temps etc.
		self._setConnected(True)
		self._logger.debug("{}@Connect: Connect OK".format(self._full_path))
		
	def dbus_Connected(self):
		return self._connected

	def dbus_Disconnect(self):
		self._logger.debug(
			"{}@Disconnect: Disconnect INIT".format(self._full_path))
		if not self._getConnected():
			self._logger.debug(
				"{}@Disconnect: Module is already disconnected".format(self._full_path))
			raise self.IOError("Module is already disconnected.")
		
		self._setConnected(False)
		self._rfm69.shutdown()
		self._logger.debug("{}@Disconnect: Disconnect OK".format(self._full_path)) 

	def dbus_Setup(self, args):
		self._logger.debug("{}@Setup: Setup INIT".format(self._full_path))
		self._setup.clear()
		self._setup = {}
		
		modemConfigTable = args.pop("MODEM_CONFIG_TABLE", MODEM_CONFIG_TABLE)
		self._setup["MODEM_CONFIG_TABLE"] = modemConfigTable
		
		modemConfig = args.pop("MODEM_CONFIG", MODEM_CONFIG)
		self._setup["MODEM_CONFIG"] = modemConfig
			
		modemKey = args.pop("key", MODEM_KEY)
		self._setup["key"] = modemKey
		
		channel = args.pop("channel", CHANNEL)
		self._setup["channel"] = channel
		
		self._logger.debug(
			"{}@Setup: Parameters={}".format(self._full_path, self._setup))
		self._logger.debug(
			"{}@Setup: Setup OK".format(self._full_path, self._setup))

	def dbus_Send(self, args):
		self._logger.debug(
			"{}@Send: Send INIT".format(self._full_path))
		
		if not self._getConnected():
			self._logger.debug(
				"{}@Send: Module is not connected".format(self._full_path))
			raise self.IOError("Module is not connected.")
		
		sendId = args.pop("ID", "")
		sendData = args.pop("DATA", "")
		
		if not sendData or not sendId:
			self._logger.debug(
				"{}@Send/Rfm69: No data or Id provided".format(self._full_path))
			raise self.ValueError("You must provide the data and Id.")
		
		if not type(sendData) is list:
			self._logger.debug(
				"{}@Send/Rfm69: Data in wrong format".format(self._full_path))
			raise self.TypeError("You must provide the data as a list of values.")
		
		# Turn it back into bytes again, since D-Bus turns it into a list
		sendData = struct.pack("B"*len(sendData), *sendData)
		self._rfm69.send(sendId, sendData)
	
	def dbus_Receive(self):
		self._logger.debug("{}@Receive: Receive INIT".format(self._full_path))
		if not self._getConnected():
			self._logger.debug(
				"{}@Receive: Module is not connected".format(self._full_path))
			raise self.IOError("Module is not connected.")
		result = {}
		
		self._rfm69.receiveBegin()
		
		# Listen for comms from bricks
		totalWait = 0
		while not self._rfm69.receiveDone() and totalWait < RECEIVE_TIMEOUT:
			time.sleep(.05)
			totalWait += .05
		
		if totalWait < RECEIVE_TIMEOUT:
			self._logger.debug("{}@Receive: receiveDone()".format(self._full_path))
			result["SENDERID"] = self._rfm69.SENDERID
			result["DATA"] = bytearray(self._rfm69.DATA)
			result["RSSI"] = self._rfm69.RSSI
		
		return result
	
	def dbus_Name(self):
		return PROTOCOL_NAME
		
	def dbus_Driver(self):
		return "No driver."
	
	def dbus_Discover(self, args):
		raise self.NotImplementedError("Function not supported.")
	
	def dbus_Exec(self, op, args):
		raise self.NotImplementedError("Function not supported.")
	
	def dbus_Subscribe(self, args):
		raise self.NotImplementedError("Function not supported.")
		