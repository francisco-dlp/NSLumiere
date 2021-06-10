import serial
import time
import logging
from . import EELS_controller
from nion.swift.model import HardwareSource

__author__ = "Yves Auad"

class EELS_Spectrometer(EELS_controller.EELSController):

    def __init__(self, sport):
        super().__init__()
        self.success = False
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = sport
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.success = True
        except:
            logging.info("***EELS SPECTROMETER***: Could not find EELS Spec. Please check hardware. "
                         "Entering in debug mode...")

    def set_val(self, val, which):
        if which=="off":
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
            if scan is not None:
                scan.scan_device.orsayscan.drift_tube = float(val)
        else:
            if which=="dmx": which="al"
            if abs(val)<32767:
                try:
                    if val < 0:
                        val = abs(val)
                    else:
                        val = 0xffff - val
                    string = which + ' 0,' + hex(val)[2:6] + '\r'
                    self.ser.write(string.encode())
                    return self.ser.read(6)
                except:
                    logging.info(
                        "***EELS SPECTROMETER***: Problem communicating over serial port. Easy check using Serial Port Monitor.")
            else:
                logging.info("***EELS SPECTROMETER***: Attempt to write a value out of range.")



