# standard libraries
import json
import os
import logging

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/global_settings.json')
with open(abs_path) as savfile:
    settings = json.load(savfile)
DEBUG = settings["diaf"]["DEBUG"]
START_DIAF = True

if DEBUG:
    from . import diaf_vi as diaf
else:
    from . import diaf as diaf


class diafDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.set_full_range = Event.Event()

        self.__sendmessage = diaf.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__apert = diaf.Diafs(self.__sendmessage)

        if START_DIAF:
            try:
                inst_dir = os.path.dirname(__file__)
                abs_path = os.path.join(inst_dir, '../aux_files/config/diafs_settings.json')
                with open(abs_path) as savfile:
                    data = json.load(savfile)  # data is load json
                self.roa_change_f = int(data['ROA']['last'])
                self.voa_change_f = int(data['VOA']['last'])

            except:
                logging.info('***APERTURES***: No saved values. Check your json file.')

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***APERTURES***: Could not find Apertures Hardware")
            if message == 2:
                logging.info("***APERTURES***: Communication problem over serial port. Easy check using Serial Port Monitor.")

        return sendMessage

    def set_values(self, value, which):
        diaf_list = ['None', '50', '100', '150']
        value = diaf_list[value]
        inst_dir = os.path.dirname(__file__)
        abs_path = os.path.join(inst_dir, '../aux_files/config/diafs_settings.json')
        with open(abs_path) as savfile:
            data = json.load(savfile)  # data is load json
        if which == 'ROA':
            self.m1_f = data[which][value]['m1']
            self.m2_f = data[which][value]['m2']
        elif which == 'VOA':
            self.m3_f = data[which][value]['m3']
            self.m4_f = data[which][value]['m4']

    @property
    def voa_change_f(self):
        return self.__voa

    @voa_change_f.setter
    def voa_change_f(self, value):
        self.set_full_range.fire()  # before change you need to let slider go anywhere so you can set the value
        self.__voa = value
        self.set_values(value, 'VOA')
        self.property_changed_event.fire('voa_change_f')

    @property
    def roa_change_f(self):
        return self.__roa

    @roa_change_f.setter
    def roa_change_f(self, value):
        self.set_full_range.fire()  # before change you need to let slider go anywhere so you can set the value
        self.__roa = value
        self.set_values(value, 'ROA')
        self.property_changed_event.fire('roa_change_f')

    @property
    def m1_f(self):
        return self.__m1

    @m1_f.setter
    def m1_f(self, value):
        self.__m1 = value
        self.__apert.set_val(1, value)
        self.property_changed_event.fire('m1_f')

    @property
    def m2_f(self):
        return self.__m2

    @m2_f.setter
    def m2_f(self, value):
        self.__m2 = value
        self.__apert.set_val(2, value)
        self.property_changed_event.fire('m2_f')

    @property
    def m3_f(self):
        return self.__m3

    @m3_f.setter
    def m3_f(self, value):
        self.__m3 = value
        self.__apert.set_val(3, value)
        self.property_changed_event.fire('m3_f')

    @property
    def m4_f(self):
        return self.__m4

    @m4_f.setter
    def m4_f(self, value):
        self.__m4 = value
        self.__apert.set_val(4, value)
        self.property_changed_event.fire('m4_f')
