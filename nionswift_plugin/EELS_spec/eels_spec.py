import serial
import sys
import time
import threading
from nion.swift.model import HardwareSource

__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class espec:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
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
            self.sendmessage(1)

    def set_val(self, val, which):
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
                self.sendmessage(2)
        else:
            self.sendmessage(3)

    def set_vsm(self, val):
        scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
        if scan is not None:
            scan.scan_device.orsayscan.drift_tube = val


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


