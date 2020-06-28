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

    def query_obj(self):
        string='>1,2,1\r'
        logging.info(string)
        self.ser.write(string.encode())
        time.sleep(0.01)
        self.ser.read(7)
        current=self.ser.read(8)
        self.ser.read(1)
        voltage=self.ser.read(8)
        self.ser.readline()
        return current, voltage
		
    def set_val(self, val, which):
        if which=='OBJ':
            string_init='>1,1,1,'
        if which=='C1':
            string_init='>1,1,2,'
        if which=='C2':
            string_init='>1,1,3,'
			
        string=string_init+str(val)+',0.5\r'
        logging.info(string)
        self.ser.write('>1,2,1\r'.encode())
        logging.info(self.ser.readline())
        time.sleep(0.01)
        if val>0:
            self.ser.write(string.encode())
            return self.ser.readline()
        else:
            self.sendmessage(2)
		
    def wobbler_loop(self, current, intensity, frequency, which):
        self.wobbler_thread=threading.currentThread()
        while getattr(self.wobbler_thread, "do_run", True):
            self.set_val(current+intensity, which)
            time.sleep(1./frequency)
            logging.info(frequency)
            self.set_val(current-intensity, which)
            time.sleep(1./frequency)
			
    def wobbler_on(self, current, intensity, frequency, which):
        self.wobbler_thread=threading.Thread(target=self.wobbler_loop, args=(current, intensity, frequency, which),)
        self.wobbler_thread.start()
		
    def wobbler_off(self):
        self.wobbler_thread.do_run=False
		
