# standard libraries
import logging
import os
import json
import threading
import numpy
import time

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)
DEBUG = settings["SPECTROMETER"]["DEBUG"]
MANUFACTURER = settings["SPECTROMETER"]["MANUFACTURER"]

if DEBUG:
    from . import spec_vi as optSpec
else:
    if MANUFACTURER=='Princeton': from . import spec as optSpec
    elif MANUFACTURER=='ATTOLIGHT': from . import spec_attolight as optSpec

class OptSpecDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.send_gratings = Event.Event()

        self.__running=False

    def init(self):
        self.__sendmessage = optSpec.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__Spec = optSpec.OptSpectrometer(2, 6, self.__sendmessage)

        self.__gratings = self.__Spec.gratingNames()
        self.send_gratings.fire(self.__gratings)
        self.__lpmms = self.__Spec.gratingLPMM()
        self.__fl = self.__Spec.get_specFL()

        return True

    def upt(self):
        self.property_changed_event.fire('wav_f')
        self.property_changed_event.fire('grating_f')
        self.property_changed_event.fire('entrance_slit_f')
        self.property_changed_event.fire('exit_slit_f')
        self.property_changed_event.fire('which_slit_f')

    def sendMessageFactory(self):
        def sendMessage(message):
            '''if message == 1:
                logging.info("***OPT SPECTROMETER***: Serial Communication was not possible. Check instrument")
            if message == 2:
                logging.info("***OPT SPECTROMETER***: Grating changed successfully.")
            if message == 3:
                logging.info("***OPT SPECTROMETER***: Wavelength changed successfully.")
            if message == 4:
                logging.info("***OPT SPECTROMETER***: Entrance slit width changed successfully.")
            if message == 5:
                logging.info("***OPT SPECTROMETER***: Exit slit width changed successfully.")
            if message == 6:
                logging.info("***OPT SPECTROMETER***: Axial/Lateral slit changed successfully.")
            if message == 7:
                logging.info("***OPT SPECTROMETER***: Attempted to set a property outside allowed range. Setting stard value..")'''
            print(message)
            if message:
                self.__running=False
                self.property_changed_event.fire("")

        return sendMessage

    @property
    def wav_f(self):
        try:
            self.__wl = self.__Spec.get_wavelength()
            return format(self.__wl, '.3f')
        except AttributeError:
            return 'None'

    @wav_f.setter
    def wav_f(self, value):
        if self.__wl != float(value):
            self.__wl = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_wavelength, args=(self.__wl,)).start()
            self.__running=True

    @property
    def grating_f(self):
        try:
            self.__grating = self.__Spec.get_grating()
            return self.__grating
        except AttributeError:
            return 0

    @grating_f.setter
    def grating_f(self, value):
        if self.__grating != value:
            self.__grating = value
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_grating, args=(self.__grating,)).start()
            self.__running = True

    @property
    def lpmm_f(self):
        return self.__lpmms[self.__grating]

    @property
    def dif_angle_f(self):
        return numpy.arcsin(self.__wl * self.lpmm_f / 1e6)

    @property
    def dispersion_f(self):
        return 1e6/self.lpmm_f * numpy.cos(self.dif_angle_f) / self.__fl

    @property
    def entrance_slit_f(self):
        try:
            self.__entrance_slit = self.__Spec.get_entrance()
            return self.__entrance_slit
        except AttributeError:
            return 'None'

    @entrance_slit_f.setter
    def entrance_slit_f(self, value):
        if self.__entrance_slit != float(value):
            self.__entrance_slit = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_entrance, args=(self.__entrance_slit,)).start()
            self.__running = True

    @property
    def exit_slit_f(self):
        try:
            self.__exit_slit = self.__Spec.get_exit()
            return self.__exit_slit
        except AttributeError:
            return 'None'

    @exit_slit_f.setter
    def exit_slit_f(self, value):
        if self.__exit_slit != float(value):
            self.__exit_slit = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_exit, args=(self.__exit_slit,)).start()
            self.__running = True

    @property
    def which_slit_f(self):
        try:
            self.__slit_choice = self.__Spec.get_which()
            return self.__slit_choice
        except AttributeError:
            return -1

    @which_slit_f.setter
    def which_slit_f(self, value):
        if self.__slit_choice != value:
            self.__slit_choice = value
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_which, args=(self.__slit_choice,)).start()
            self.__running = True