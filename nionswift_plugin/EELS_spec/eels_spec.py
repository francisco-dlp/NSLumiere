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

class espec:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate=9600
        self.ser.port='COM4'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=2
		
        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.5)
        except:
            self.sendmessage(1)

    def set_val(self, val, which):
        if val<0: val=0xffff+val
        string = which+' 0,'+hex(val)[2:6]+'\r'	
        time.sleep(0.01)
        self.ser.write(string.encode())
        return self.ser.read(6)
