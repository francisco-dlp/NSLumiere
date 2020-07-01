# standard libraries
import os
import json
import math
import numpy
import os
import random
import scipy.ndimage.interpolation
import scipy.stats
import threading
import typing
import time
from nion.data import Calibration
from nion.data import DataAndMetadata
import asyncio
import logging
import queue

from nion.utils import Registry
from nion.utils import Event
from nion.utils import Geometry
from nion.utils import Model
from nion.utils import Observable
from nion.swift.model import HardwareSource
from nion.swift.model import ImportExportManager

import logging
import time
import sys

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
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG Scan***: TEST")

        return sendMessage

    @property
    def field_f(self):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        logging.info(self.__OrsayScanInstrument.scan_device.orsayscan.GetFieldSize())
        return int(self.__field*2e10)

    @field_f.setter
    def field_f(self, value):
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        self.__field=value/2e10
        logging.info(self.__OrsayScanInstrument.scan_device.orsayscan.SetFieldSize(self.__field))
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

