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


class OptMonochromator:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM16'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 30

        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.1)

                self.ser.write(b'?NM\r')
                wav_line = ser.readline()
                self.wavelength = float(wav_line[1:6].decode())

                self.ser.write(b'?GRATING\r')
                grating_line = ser.readline()
                self.now_grating = int(grating_line[1:2].decode())

                self.ser.write(b'EXIT-MIRROR ?MIRROR\r')
                mirror_line = ser.readline()
                if mirror_line[1:6].decode() == 'front':
                    self.which_slit=0
                else:
                    self.which_slit=1

                self.ser.write(b'SIDE-ENT-SLIT ?MICRONS\r')
                entrance_line = ser.readline()
                self.entrance_slit = float(entrance_line[1:5].decode())

                self.ser.write(b'SIDE-EXIT-SLIT ?MICRONS\r')
                exit_line = ser.readline()
                self.exit_slit = float(exit_line[1:5].decode())



        except:
            self.sendmessage(1)

    def set_grating(self, value):

        self.sendmessage(2)

    def set_wavelength(self, value):

        self.sendmessage(3)

    def set_entrance(self, value):

        self.sendmessage(4)

    def set_exit(self, value):

        self.sendmessage(5)

    def set_which(self, value):

        self.sendmessage(6)