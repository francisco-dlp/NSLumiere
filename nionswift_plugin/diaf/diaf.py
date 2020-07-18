import serial
import sys
import logging
import time
import threading
import numpy
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

__author__ = "Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3


def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class Diafs:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
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
                time.sleep(0.1)
        except:
            self.sendmessage(1)

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
            self.sendmessage(2)
