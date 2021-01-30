import json
import os
import logging

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)
DEBUG = settings["diaf"]["DEBUG"]

if DEBUG:
    from . import diaf_vi as diaf
else:
    from . import diaf as diaf


class diafDevice(Observable.Observable):

    def __init__(self, dict):
        self.property_changed_event = Event.Event()
        self.busy_event = Event.Event()
        self.set_full_range = Event.Event()

        self.__apert = diaf.Diafs()
        self.__apertDict = dict
        self.__keys = list(dict.keys())

        """
        Index represents which aperture is on. Values are the X-Y values of the 
        current aperture.
        """
        self.__index = [0] * len(dict)
        self.__values = [0] * len(dict) * 2

        try:
            inst_dir = os.path.dirname(__file__)
            abs_path = os.path.join(inst_dir, 'diafs_settings.json')
            with open(abs_path) as savfile:
                data = json.load(savfile)  # data is load json
            self.roa_change_f = int(data[self.__keys[0]]['last'])
            self.voa_change_f = int(data[self.__keys[1]]['last'])
        except:
            logging.info('***APERTURES***: No saved values. Check your json file.')

    def set_values(self, value, which):
        diaf_list = self.__apertDict[which]
        value = diaf_list[value]
        inst_dir = os.path.dirname(__file__)
        abs_path = os.path.join(inst_dir, 'diafs_settings.json')
        with open(abs_path) as savfile:
            data = json.load(savfile)  # data is load json
        if which == self.__keys[0]:
            self.m1_f = data[which][value]['m1']
            self.m2_f = data[which][value]['m2']
        elif which == self.__keys[1]:
            self.m3_f = data[which][value]['m3']
            self.m4_f = data[which][value]['m4']

    @property
    def voa_change_f(self):
        return self.__index[1]

    @voa_change_f.setter
    def voa_change_f(self, value):
        self.set_full_range.fire()  # before change you need to let slider go anywhere so you can set the value
        self.__index[1] = value
        self.set_values(value, self.__keys[1])
        self.property_changed_event.fire('voa_change_f')

    @property
    def roa_change_f(self):
        return self.__index[0]

    @roa_change_f.setter
    def roa_change_f(self, value):
        self.set_full_range.fire()  # before change you need to let slider go anywhere so you can set the value
        self.__index[0] = value
        self.set_values(value, self.__keys[0])
        self.property_changed_event.fire('roa_change_f')

    @property
    def m1_f(self):
        return self.__values[0]

    @m1_f.setter
    def m1_f(self, value):
        self.__values[0] = value
        self.__apert.set_val(1, value)
        self.property_changed_event.fire('m1_f')

    @property
    def m2_f(self):
        return self.__values[1]

    @m2_f.setter
    def m2_f(self, value):
        self.__values[1] = value
        self.__apert.set_val(2, value)
        self.property_changed_event.fire('m2_f')

    @property
    def m3_f(self):
        return self.__values[2]

    @m3_f.setter
    def m3_f(self, value):
        self.__values[2] = value
        self.__apert.set_val(3, value)
        self.property_changed_event.fire('m3_f')

    @property
    def m4_f(self):
        return self.__values[3]

    @m4_f.setter
    def m4_f(self, value):
        self.__values[3] = value
        self.__apert.set_val(4, value)
        self.property_changed_event.fire('m4_f')
