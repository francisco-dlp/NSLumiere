import serial
import sys
import time
import threading
import os
import json
import logging

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

MAX_OBJ = settings["lenses"]["MAX_OBJ"]
MAX_C1 = settings["lenses"]["MAX_C1"]
MAX_C2 = settings["lenses"]["MAX_C2"]

__author__ = "Yves Auad"

class Lenses:

    def __init__(self):
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
            logging.info("***LENSES***: Could not find Lenses PS")

        self.ser.readline()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        with self.lock:
            try:
                self.ser.write(string.encode())
                self.ser.read(7)
                current = self.ser.read_until(expected=b','); current = current[:-1]
                voltage = self.ser.read_until(expected=b','); voltage = voltage[:-1]
                self.ser.readline()
            except:
                logging.info('***LENSES***: Communication Error over Serial Port. Easy check using Serial Port '
                             'Monitor software.')
        return current, voltage

    def set_val(self, val, which):
        if which == 'OBJ' and val<=MAX_OBJ and val>=0:
            string_init = '>1,1,1,'
        elif which == 'C1' and val<=MAX_C1 and val>=0:
            string_init = '>1,1,2,'
        elif which == 'C2' and val<=MAX_C2 and val>=0:
            string_init = '>1,1,3,'
        else:
            logging.info("***LENSES***: Attempt to set values out of range.")
            return None

        string = string_init + str(val) + ',0.5\r'
        with self.lock:
            self.ser.write(string.encode())
            return self.ser.readline()

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
