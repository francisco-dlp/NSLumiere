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

    def query(self, string):
        if string=='0010074002=?106\r':
            return (numpy.random.randn(1)[0]+2)*1e-1
        else:
            None


    
		
