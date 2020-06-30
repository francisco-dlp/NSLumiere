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

class AirLockVacuum:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage
        self.ser=serial.Serial()
        self.ser.baudrate=9600
        self.ser.port='COM6'
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=2

        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.1)
        except:
            self.sendmessage(4)


    def query(self):
        try:
            self.ser.write(b'0010074002=?106\r')
            self.ser.read(10)
            data=self.ser.read(4).decode()
            ex=self.ser.read(2).decode()
            self.ser.read(4)
            value = int(data)/1000. * 10**(int(ex)-20)
            return value
        except:
            return 0.0


    
		
