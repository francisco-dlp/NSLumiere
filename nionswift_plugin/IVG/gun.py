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
        self.ser.baudrate=115200
        self.ser.port='COM5'
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.1)
            self.ser.write(b'GDAT? 1\n')
            self.ser.readline()
        except:
            self.sendmessage(3)



    def query(self):
        try:
            self.ser.write(b'GDAT? 1\n')
            value=self.ser.read(15)
            value=value.decode()
            ex=int(value[-5:-1])
            sig=float(value[0:6])
            vide=sig * 10**ex
            return vide
        except:
            return 0


    
		
