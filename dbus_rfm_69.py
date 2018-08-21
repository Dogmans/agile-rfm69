#!/usr/bin/env python2
# --- Imports -----------
import logging
import struct
import time

from twisted.internet import reactor, defer
from txdbus import client, objects, error
from txdbus.interface import DBusInterface, Method

from config import *
import rfm69
from rfm69.constants import RF
	
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
			self._rfm69.spi_write(address, value)
			
	def _setModemKey(self):
		self._logger.debug("enabling ecryption")
		self._rfm69.set_encryption(self._setup["key"])
		
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
		self._rfm69 = rfm69.RFM69(25, 24, 0, rfm69.RFM69Configuration(), True)
		self._rfm69.set_channel(self._setup["channel"])
		self._rfm69.set_address(1)
		
		self._logger.debug("Class initialized")
		self._logger.debug("Calibrating RSSI")
		# self._rfm69.calibrate_rssi_threshold()
		self._logger.debug("Checking temperature")
		self._logger.debug(self._rfm69.read_temperature())
		
		# Make sure settings are correct to talk to other radios
		self._setModemConfig()
		self._setModemKey()
		
		self._logger.debug("reading all registers")
		for result in self._rfm69.read_registers():
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
		self._rfm69.disconnect()
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
		
		sendData = args.pop("DATA", "")
		
		if not sendData:
			self._logger.debug(
				"{}@Send/Rfm69: No data provided".format(self._full_path))
			raise self.ValueError("You must provide the data.")
		
		if not type(sendData) is list:
			self._logger.debug(
				"{}@Send/Rfm69: Data in wrong format".format(self._full_path))
			raise self.TypeError("You must provide the data as a list of values.")
		
		# Turn it back into bytes again, since D-Bus turns it into a list
		sendData = struct.pack("B"*len(sendData), *sendData)
		self._rfm69.send_packet(sendData)
	
	def dbus_Receive(self):
		self._logger.debug("{}@Receive: Receive INIT".format(self._full_path))
		if not self._getConnected():
			self._logger.debug(
				"{}@Receive: Module is not connected".format(self._full_path))
			raise self.IOError("Module is not connected.")
		
		result = {}
		(data, rssi) = self._rfm69.wait_for_packet()
		
		if data:
			self._logger.debug("{}@Receive: receiveDone()".format(self._full_path))
			result["DATA"] = data
			result["RSSI"] = rssi
		
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
		