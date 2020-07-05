# standard libraries
import logging
import os
import json

from nion.utils import Event
from nion.utils import Observable
from nion.swift.model import HardwareSource

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

DEBUG = settings["Scan_Lum"]["DEBUG"]

class scanDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__field=0.00004

        self.__OrsayScanInstrument = None


        #self.__sendmessage = lens_ps.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        #self.__lenses_ps = lens_ps.Lenses(self.__sendmessage)

    def get_orsay_scan_instrument(self):
        if not DEBUG:
            self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
        else:
            pass #Here is debug

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG Scan***: TEST")

        return sendMessage

    @property
    def field_f(self):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        if not DEBUG: self.__OrsayScanInstrument.scan_device.orsayscan.GetFieldSize()
        return int(self.__field*2e10)

    @field_f.setter
    def field_f(self, value):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        self.__field=value/2e10
        if not DEBUG: self.__OrsayScanInstrument.scan_device.orsayscan.SetFieldSize(self.__field)
        self.property_changed_event.fire('field_f')
        self.property_changed_event.fire('field_edit_f')

    @property
    def field_edit_f(self):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        return str(self.__field)

    @field_edit_f.setter
    def field_edit_f(self, value):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        self.__field = float(value)
        self.property_changed_event.fire('field_f')
        self.property_changed_event.fire('field_edit_f')

