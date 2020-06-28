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

    def set_val(self, val, which):
        if val<0: val=0xffff+val
        string = which+' 0,'+hex(val)[2:6]+'\r'	
        logging.info(string)
        time.sleep(0.01)
        return None
