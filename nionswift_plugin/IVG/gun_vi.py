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

    def query(self, string):
        if string=='GDAT? 1\n':
            return (str('{:.2E}'.format((numpy.random.randn(1)[0]+2)*1e-10))+ ' mTorr').encode()
        else:
            None


    
		
