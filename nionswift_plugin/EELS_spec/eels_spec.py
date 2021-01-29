import serial
import time
import threading

__author__ = "Yves Auad"

class espec:

    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM4'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.1)
        except:
            logging.info("***EELS SPECTROMETER***: Could not find EELS Spec. Check Hardware")

    def set_spec_val(self, val, which):
        if abs(val)<32767:
            try:
                if val < 0:
                    val = abs(val)
                else:
                    val = 0xffff - val
                string = which + ' 0,' + hex(val)[2:6] + '\r'
                self.ser.write(string.encode())
                return self.ser.read(6)
            except:
                logging.info(
                    "***EELS SPECTROMETER***: Problem communicating over serial port. Easy check using Serial Port Monitor.")
        else:
            logging.info("***EELS SPECTROMETER***: Attempt to write a value out of range.")

    def wobbler_loop(self, current, intensity, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.set_spec_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.set_spec_val(current, which)

    def wobbler_on(self, current, intensity, which):
        self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, which), )
        self.wobbler_thread.start()

    def wobbler_off(self):
        self.wobbler_thread.do_run = False


