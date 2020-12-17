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


    def get_wavelength(self):
        return self.wavelength

    def set_wavelength(self, value):
        self.wavelength = value
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(3)

    def get_grating(self):
        return self.now_grating

    def set_grating(self, value):
        self.now_grating = value
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(2)

    def get_entrance(self):
        return self.entrance_slit

    def set_entrance(self, value):
        self.entrance_slit = value
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(4)

    def get_exit(self):
        return self.exit_slit

    def set_exit(self, value):
        self.exit_slit = value
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(5)

    def get_which(self):
        return self.which_slit

    def set_which(self, value):
        self.which_slit = value
        a = abs(numpy.random.randn(1)[0] * 5)
        time.sleep(a + 1)
        self.sendmessage(6)

    def gratingNames(self):
        return [
            "300 g/mm BLZ=  300NM",
            "300 g/mm BLZ=  1.0UM",
            "150 g/mm BLZ=  500NM"
        ]
