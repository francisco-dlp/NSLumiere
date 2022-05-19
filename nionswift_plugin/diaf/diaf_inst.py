# standard libraries
import logging

from nion.utils import Event
from nion.utils import Observable
from ..aux_files import read_data

set_file = read_data.FileManager('global_settings')
SERIAL_PORT = set_file.settings["diaf"]["COM"]
START_DIAF = True

from . import diaf as diaf

class diafDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.set_full_range = Event.Event()
        self.__data = read_data.FileManager('diafs_settings')

        self.__apert = diaf.Diafs(SERIAL_PORT)
        if not self.__apert.succesfull:
            from . import diaf_vi
            self.__apert = diaf_vi.Diafs()

        if START_DIAF:
            try:
                self.roa_change_f = int(self.__data.settings['ROA']['last'])
                self.voa_change_f = int(self.__data.settings['VOA']['last'])
            except:
                logging.info('***APERTURES***: No saved values. Check your json file.')

    def set_values(self, value, which):
        diaf_list = ['None', '50', '100', '150']
        value = diaf_list[value]
        if which == 'ROA':
            self.m1_f = self.__data.settings[which][value]['m1']
            self.m2_f = self.__data.settings[which][value]['m2']
        elif which == 'VOA':
            self.m3_f = self.__data.settings[which][value]['m3']
            self.m4_f = self.__data.settings[which][value]['m4']

    def save_values(self, value, which):
        if which == 'ROA':
            self.__data.settings[which][value]['m1'] = self.m1_f
            self.__data.settings[which][value]['m2'] = self.m2_f
        elif which == 'VOA':
            self.__data.settings[which][value]['m3'] = self.m3_f
            self.__data.settings[which][value]['m4'] = self.m4_f

        self.__data.save_locally()

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
