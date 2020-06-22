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

class Lenses:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate=57600
        self.ser.port='COM13'
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
		
        self.ser.readline()

		
    def set_val(self, val, which):
        if which=='OBJ':
            string_init='>1,1,1,'
        if which=='C1':
            string_init='>1,1,2,'
        if which=='C2':
            string_init='>1,1,3,'
			
        string=string_init+str(val)+',0.5\r'
        logging.info(string)
        time.sleep(0.01)
        self.ser.write(string.encode())
        return self.ser.readline()
		