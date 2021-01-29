import sys
import logging
import time
import threading
import numpy

#from . import lens_controller

__author__ = "Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3


def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class Lenses():

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
        self.lock = threading.Lock()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        current = str(abs(numpy.random.randn(1)[0]) * 0.01 + 7.5).encode()
        voltage = str(abs(numpy.random.randn(1)[0]) * 0.1 + 42.5).encode()
        return current, voltage

    def locked_query(self, which):
        with self.lock:
            return self.query(which)

    def set_val(self, val, which):
        if which == 'OBJ':
            string_init = '>1,1,1,'
        if which == 'C1':
            string_init = '>1,1,2,'
        if which == 'C2':
            string_init = '>1,1,3,'
        string = string_init + str(val) + ',0.5\r'
        logging.info(string)
        if val < 0:
            self.sendmessage(2)

    def locked_set_val(self, val, which):
        with self.lock:
            return self.set_val(val, which)


    def wobbler_loop(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.locked_set_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.locked_set_val(current, which)

    def wobbler_on(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, frequency, which), )
        self.wobbler_thread.start()

    def wobbler_off(self):
        self.wobbler_thread.do_run = False


