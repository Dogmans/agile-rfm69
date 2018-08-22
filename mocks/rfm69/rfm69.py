from __future__ import division, absolute_import, print_function, unicode_literals
from time import sleep, time
import logging
import struct

from .configuration import IRQFlags1, IRQFlags2, OpMode, Temperature1, RSSIConfig
from .constants import Register, RF


class RadioError(Exception):
    pass


def wait_for(condition, timeout=5, check_time=0.005):
    """ Wait for a radio condition to become true within a timeout.
        If this doesn't happen, raise a RadioError.

        Returns the amount of time """
    start = time()
    return start


class RFM69(object):
    """ Interface for the RFM69 series of radio modules. """
    def __init__(self, reset_pin=None, dio0_pin=None, spi_channel=None, config=None, high_power=False):
        """ Initialise the object and configure the receiver.

            reset_pin -- the GPIO pin number which is attached to the reset pin of the RFM69
            dio0_pin  -- the GPIO pin number which is attached to the DIO0 pin of the RFM69
            spi_channel -- the SPI channel used by the RFM69
            config    -- an instance of `RFM69Configuration`
        """
        self.log = logging.getLogger(__name__)
        self.reset_pin = reset_pin
        self.dio0_pin = dio0_pin
        self.spi_channel = spi_channel
        self.config = config
        self.high_power = high_power
        self.rx_restarts = 0
        self.log.info("Initialised successfully")

    def wait_for_packet(self, timeout=None):
        # sleep(5)
        return (bytearray([1, 3, 0, 0, 9, 0, 0, 0, 0, 0, 0, 86, 241, 2, 0, 15, 161]), -30)

    def send_packet(self, data, preamble=None):
        pass

    def set_mode(self, mode, wait=True):
        pass

    def set_encryption(self, key):
        pass

    def set_channel(self, value):
        pass

    def set_address(self, value):
        pass

    def set_high_power(self, on):
        pass

    def get_rssi(self):
        return -30

    def get_rssi_threshold(self):
        return -100

    def set_rssi_threshold(self, value):
        pass

    def calibrate_rssi_threshold(self, samples=10):
        pass

    def read_temperature(self):
        return 21

    def read_register(self, register_cls):
        return 0

    def read_registers(self):
        for register in range(1, 0x50):
            yield 0

    def disconnect(self):
        pass

    def spi_write(self, address, value):
        pass
