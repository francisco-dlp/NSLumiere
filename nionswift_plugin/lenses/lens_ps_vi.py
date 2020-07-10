import serial
import sys
import logging
import time
import threading
import numpy



__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class Lenses:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage
        self.lock = threading.Lock()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        with self.lock:
            current = str(abs(numpy.random.randn(1)[0])+7.5).encode()
            voltage = str(abs(numpy.random.randn(1)[0])+50.0).encode()
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
        with self.lock:
            if val<0:
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
