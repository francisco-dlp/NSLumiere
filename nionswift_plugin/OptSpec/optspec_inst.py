# standard libraries
import logging
import os
import json
import threading
import numpy

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)
DEBUG = settings["SPECTROMETER"]["DEBUG"]

if DEBUG:
    from . import spec_vi as optSpec
else:
    from . import spec as optSpec

class OptSpecDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__sendmessage = optSpec.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__Spec = optSpec.OptSpectrometer(self.__sendmessage)

        self.__wl = self.__Spec.wavelength
        self.__grating = self.__Spec.now_grating
        self.__entrance_slit = self.__Spec.entrance_slit
        self.__exit_slit = self.__Spec.exit_slit
        self.__slit_choice = self.__Spec.which_slit

        self.__lp_mm=self.__Spec.lp_mm[self.__grating]
        self.__dif=numpy.arcsin(self.__wl * self.__lp_mm / 1e6)
        self.__disp = 1e6/self.__lp_mm * numpy.cos(self.__dif) / 320

        self.__running=False

    def init(self):
        logging.info('***MONOCHROMATOR***: Initializing hardware...')


    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***Monochromator***: Serial Communication was not possible. Check instrument")
            if message == 2:
                logging.info("***MONOCHROMATOR***: Grating changed successfully.")
            if message == 3:
                logging.info("***MONOCHROMATOR***: Wavelength changed successfully.")
            if message == 4:
                logging.info("***MONOCHROMATOR***: Entrance slit width changed successfully.")
            if message == 5:
                logging.info("***MONOCHROMATOR***: Exit slit width changed successfully.")
            if message == 6:
                logging.info("***MONOCHROMATOR***: Axial/Lateral slit changed successfully.")
            if message == 7:
                logging.info("***MONOCHROMATOR***: Attempted to set a property outside allowed range. Setting stard value..")
            self.__running=False
            self.property_changed_event.fire("")

        return sendMessage

    @property
    def wav_f(self):
        return self.__wl

    @wav_f.setter
    def wav_f(self, value):
        self.__wl=float(value)
        self.__dif=numpy.arcsin(self.__wl * self.__lp_mm / 1e6)
        self.busy_event.fire("")
        if not self.__running: threading.Thread(target=self.__Spec.set_wavelength, args=(self.__wl,)).start()
        self.__running=True

    @property
    def grating_f(self):
        return self.__grating

    @grating_f.setter
    def grating_f(self, value):
        self.__grating = value
        self.__lp_mm=self.__Spec.lp_mm[self.__grating]
        self.__dif=numpy.arcsin(self.__wl * self.__lp_mm / 1e6)
        self.busy_event.fire("")
        if not self.__running: threading.Thread(target=self.__Spec.set_grating, args=(self.__grating,)).start()
        self.__running = True

    @property
    def lp_mm_f(self):
        return self.__lp_mm

    @property
    def dif_angle_f(self):
        return self.__dif

    @property
    def dispersion_f(self):
        self.__disp = 1e6/self.__lp_mm * numpy.cos(self.__dif) / 320
        return self.__disp

    @property
    def entrance_slit_f(self):
        return self.__entrance_slit

    @entrance_slit_f.setter
    def entrance_slit_f(self, value):
        self.__entrance_slit = float(value)
        self.busy_event.fire("")
        if not self.__running: threading.Thread(target=self.__Spec.set_entrance, args=(self.__entrance_slit,)).start()
        self.__running = True

    @property
    def exit_slit_f(self):
        return self.__exit_slit

    @exit_slit_f.setter
    def exit_slit_f(self, value):
        self.__exit_slit = float(value)
        self.busy_event.fire("")
        if not self.__running: threading.Thread(target=self.__Spec.set_exit, args=(self.__exit_slit,)).start()
        self.__running = True

    @property
    def which_slit_f(self):
        return self.__slit_choice

    @which_slit_f.setter
    def which_slit_f(self, value):
        self.__slit_choice = value
        self.busy_event.fire("")
        if not self.__running: threading.Thread(target=self.__Spec.set_which, args=(self.__slit_choice,)).start()
        self.__running = True
