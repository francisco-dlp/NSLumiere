import serial
import sys
import logging
import time
import threading

__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class espec:

    def __init__(self, sendmessage):
        self.sendmessage=sendmessage

    def set_val(self, val, which):
        if abs(val)<32767:
            if val<0: val=0xffff+val
            string = which+' 0,'+hex(val)[2:6]+'\r'
            logging.info(string)
            return None
        else:
            self.sendmessage(3)

    def wobbler_loop(self, current, intensity, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.set_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.set_val(current, which)

    def wobbler_on(self, current, intensity, which):
        self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, which), )
        self.wobbler_thread.start()

    def wobbler_off(self):
        self.wobbler_thread.do_run = False
