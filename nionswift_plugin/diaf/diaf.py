import serial
import numpy

from . import Apertures_controller

__author__ = "Yves Auad"

class Diafs(Apertures_controller.Aperture_Controller):

    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM7'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
        except:
            logging.info("***APERTURES***: Could not find Apertures Hardware")

        self.ser.readline()

    def pos_to_bytes(self, pos):
        rem = pos
        val = numpy.zeros(4, dtype=int)
        for j in range(4):  # 4 bytes
            val[j] = rem % 256
            rem = rem - val[j]
            rem = rem / 256
        return val

    def set_val(self, motor, value):
        try:
            byt = self.pos_to_bytes(value)
            message = [motor, 20, byt[0], byt[1], byt[2], byt[3]]
            byt_array = bytearray(message)
            self.ser.write(byt_array)
            self.ser.read(6)
        except:
            logging.info("***APERTURES***: Communication problem over serial port. Easy check using Serial Port Monitor.")

    def get_val(self, which):
        pass