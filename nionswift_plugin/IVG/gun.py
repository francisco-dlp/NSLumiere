import serial
import logging
import time
import threading
import numpy

__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class GunVacuum:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage
        self.ser=serial.Serial()
        self.ser.baudrate=9600
        self.ser.port='COM5'
        self.ser.parity=serial.PARITY_ONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=2

        try:
            if not self.ser.open():
                self.ser.open()
                time.sleep(0.5)
        except:
            self.sendmessage(3)


    def query(self, string):
        self.ser.write(string.encode())
        return self.ser.readline()


    
		
