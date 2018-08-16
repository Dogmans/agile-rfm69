#!/usr/bin/env python2
import logging
import unittest
from RFM69 import RFM69
from RFM69.RFM69registers import *

class GpioTestCase(unittest.TestCase):

	def setUp(self):
		self._logger = logging.getLogger()
		self._logger.setLevel(logging.DEBUG)
		self._logger.addHandler(logging.StreamHandler())
		unittest.TestCase.setUp(self)

	def tearDown(self):
		unittest.TestCase.tearDown(self)
		del self._rfm69

	def test_ReadRegisters(self):
		self._rfm69 = RFM69.RFM69(RF69_868MHZ, 1, 99, True, 18, 22)
		results = self._rfm69.readAllRegs()
		for result in results:
			self._logger.debug(result)

if __name__ == '__main__':
	unittest.main()