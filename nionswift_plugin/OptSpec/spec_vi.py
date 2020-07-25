import sys
import time
import numpy
import os
import json

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)
LP_MM = settings["SPECTROMETER"]["GRATINGS"]["LP_MM"]

__author__ = "Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3


def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class OptSpectrometer:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
        self.wavelength = 550.
        self.now_grating = 0
        self.entrance_slit = 3000
        self.exit_slit = 3000
        self.which_slit = 1
        self.lp_mm=LP_MM

    def set_grating(self, value):
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(2)

    def set_wavelength(self, value):
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(3)

    def set_entrance(self, value):
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(4)

    def set_exit(self, value):
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(5)

    def set_which(self, value):
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(6)
