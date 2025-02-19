import logging
import time
import board
import busio
from adafruit_bus_device.spi_device import SPIDevice
from ax5043_driver import Ax5043
from ax5043_manager import Manager

logging.basicConfig(level=logging.DEBUG)
driver = Ax5043(SPIDevice(busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)))
mgr = Manager(driver)
