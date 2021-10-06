import sys
import time
import numpy

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

    def get_wavelength(self):
        return self.wavelength + self.wavelength*numpy.random.randn(1)[0]/1e5

    def set_wavelength(self, value):
        self.wavelength = value
        a = abs(numpy.random.randn(1)[0] )
        time.sleep(a + 1)
        self.sendmessage(3)

    def get_grating(self):
        return self.now_grating

    def set_grating(self, value):
        self.now_grating = value
        a = abs(numpy.random.randn(1)[0])
        time.sleep(a + 1)
        self.sendmessage(2)

    def get_entrance(self):
        return self.entrance_slit

    def set_entrance(self, value):
        self.entrance_slit = value
        a = abs(numpy.random.randn(1)[0])
        time.sleep(a + 1)
        self.sendmessage(4)

    def get_exit(self):
        return self.exit_slit

    def set_exit(self, value):
        self.exit_slit = value
        a = abs(numpy.random.randn(1)[0])
        time.sleep(a + 1)
        self.sendmessage(5)

    def get_which(self):
        return self.which_slit

    def set_which(self, value):
        self.which_slit = value
        a = abs(numpy.random.randn(1)[0])
        time.sleep(a + 1)
        self.sendmessage(6)

    def gratingNames(self):
        return [
            "600 g/mm BLZ=  300NM",
            "300 g/mm BLZ=  500NM",
            "150 g/mm BLZ=  500NM"
        ]

    def gratingLPMM(self):
        return [
            600.0,
            300.0,
            150.0
        ]

    def get_specFL(self):
        return 300.0

    def which_camera(self):
        return 'orsay_camera_eire'

    def camera_pixels(self):
        return 1024

    def deviation_angle(self):
        return 0.53