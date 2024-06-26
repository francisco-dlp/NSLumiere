import serial
import sys
import numpy
import logging

__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3

class Diafs:

    def __init__(self, sport):
        self.succesfull = False
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
            self.succesfull = True
            #self.set_home()
        except:
            logging.info("***APERTURES***: Could not find apertures hardware. Entering in debug mode.")

    def pos_to_bytes(self, pos):
        rem = pos
        val = numpy.zeros(4, dtype=int)
        for j in range(4):  # 4 bytes
            val[j] = rem % 256
            rem = rem - val[j]
            rem = rem / 256
        return val

    def set_maximum_pos(self, motor):
        pass

    def set_home(self):
        for motor in range(4):
            try:
                message = [motor, 1, 0, 0, 0, 0]
                byt_array = bytearray(message)
                self.ser.write(byt_array)
                self.ser.read(6)
            except:
                logging.info(
                    "***APERTURES***: Communication problem over serial port. Easy check using Serial Port Monitor.")

    def set_val(self, motor, value):
        try:
            byt = self.pos_to_bytes(value)
            message = [motor, 20, byt[0], byt[1], byt[2], byt[3]]
            byt_array = bytearray(message)
            self.ser.write(byt_array)
            self.ser.read(6)
        except:
            logging.info(
                "***APERTURES***: Communication problem over serial port. Easy check using Serial Port Monitor.")
