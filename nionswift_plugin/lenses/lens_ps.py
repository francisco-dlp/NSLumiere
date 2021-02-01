import serial
import sys
import time
import threading
import os
import json

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

MAX_OBJ = settings["lenses"]["MAX_OBJ"]
MAX_C1 = settings["lenses"]["MAX_C1"]
MAX_C2 = settings["lenses"]["MAX_C2"]


__author__ = "Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3


def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class Lenses:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate = 57600
        self.ser.port = 'COM13'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        self.lock = threading.Lock()

        try:
            if not self.ser.is_open:
                self.ser.open()
        except:
            self.sendmessage(1)

        self.ser.readline()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        try:
            self.ser.write(string.encode())
            self.ser.read(7)
            current = self.ser.read_until(expected=b','); current = current[:-1]
            voltage = self.ser.read_until(expected=b','); voltage = voltage[:-1]
            self.ser.readline()
        except:
            self.sendmessage(4)
        return current, voltage

    def locked_query(self, which):
        with self.lock:
            return self.query(which)

    def set_val(self, val, which):
        if which == 'OBJ' and val<=MAX_OBJ and val>=0:
            string_init = '>1,1,1,'
        elif which == 'C1' and val<=MAX_C1 and val>=0:
            string_init = '>1,1,2,'
        elif which == 'C2' and val<=MAX_C2 and val>=0:
            string_init = '>1,1,3,'
        else:
            self.sendmessage(2)
            return None

        string = string_init + str(val) + ',0.5\r'
        self.ser.write(string.encode())
        return self.ser.readline()

    def locked_set_val(self, val, which):
        with self.lock:
            return self.set_val(val, which)

    def wobbler_loop(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.set_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.set_val(current, which)

    def wobbler_on(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, frequency, which), )
        self.wobbler_thread.start()

    def wobbler_off(self):
        self.wobbler_thread.do_run = False
