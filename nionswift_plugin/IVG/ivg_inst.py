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
#from pydevd import settrace
import logging


from nion.utils import Registry
from nion.utils import Event
from nion.utils import Geometry
from nion.utils import Model
from nion.utils import Observable
from nion.swift.model import HardwareSource
from nion.swift.model import ImportExportManager


import logging
import time

DEBUG=1

if DEBUG:
    from . import ivg_vi as ivg
else:
    from . import ivg as ivg

class ivgDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.communicating_event = Event.Event()
        #self.property_changed_event_listener = self.property_changed_event.listen(self.computeCalibration)
        self.busy_event=Event.Event()
        
        self.__EHT=3
        self.__gun_vac=1.e-11
        self.__LL_vac=1.e-6
        self.__obj_cur=5
        self.__obj_vol=30
        self.__obj_temp=60

        self.__lensInstrument=None
        self.__EELSInstrument=None
		
        self.__sendmessage = ivg.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__ivg= ivg.IVG(self.__sendmessage)

    def get_lenses_instrument(self):
        self.__lensInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("lenses_controller")
    
    def get_EELS_instrument(self):
        self.__EELSInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("eels_spec_controller")
		
    def sendMessageFactory(self):
        def sendMessage(message):
            if message==1:
                logging.info("***IVG***: Could not find some or all of the hardwares")

        return sendMessage

		
    @property
    def EHT_f(self):
        return self.__EHT
		
    @EHT_f.setter
    def EHT_f(self, value):
        self.__EHT=value
        if not self.__lensInstrument:
            self.get_lenses_instrument()
        if not self.__EELSInstrument:
            self.get_EELS_instrument()
        self.__lensInstrument.EHT_change(value)
        self.__EELSInstrument.EHT_change(value)
        self.property_changed_event.fire('EHT_f')
		
    @property
    def gun_vac_f(self):
        return self.__gun_vac
		
    @gun_vac_f.setter 
    def gun_vac_f(self, value):
        self.__gun_vac=value
        self.property_changed_event.fire('gun_vac_f')
			
    @property
    def LL_vac_f(self):
        return self.__LL_vac
		
    @LL_vac_f.setter
    def LL_vac_f(self, value):
        self.__LL_vac=value
        self.property_changed_event.fire('LL_vac_f')
    
    @property
    def obj_cur_f(self):
        return self.__obj_cur
		
    @obj_cur_f.setter
    def obj_cur_f(self, value):
        self.__obj_cur=value
        self.property_changed_event.fire('obj_cur_f')
    
    @property
    def obj_vol_f(self):
        return self.__obj_vol
		
    @obj_vol_f.setter
    def obj_vol_f(self, value):
        self.__obj_vol=value
        self.property_changed_event.fire('obj_vol_f')
        
    @property
    def obj_temp_f(self):
        return self.__obj_temp
		
    @obj_temp_f.setter
    def obj_temp_f(self, value):
        self.__obj_temp=value
        self.property_changed_event.fire('obj_temp_f')
