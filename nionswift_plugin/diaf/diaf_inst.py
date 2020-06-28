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
    from . import diaf_vi as diaf
else:
    from . import diaf as diaf

class diafDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        #self.property_changed_event_listener = self.property_changed_event.listen(self.computeCalibration)
        self.busy_event=Event.Event()
        self.set_full_range=Event.Event()
        

			
		
        self.__sendmessage = diaf.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__apert = diaf.Diafs(self.__sendmessage)
				
		
        try:
            inst_dir=os.path.dirname(__file__)
            abs_path=os.path.join(inst_dir, 'diafs_settings.json')
            with open(abs_path) as savfile:
                data=json.load(savfile) #data is load json
            logging.info(json.dumps(data, indent=4))
            self.roa_change_f=int(data['ROA']['last'])
            self.voa_change_f=int(data['VOA']['last'])
			 
        except:
            logging.info('***APERTURES***: No saved values.')
			

    def sendMessageFactory(self):
        def sendMessage(message):
            if message==1:
                logging.info("Could not find Apertures Hardware")

        return sendMessage
		
    def set_values(self, value, which):
        diaf_list=['None', '50', '100', '150']
        value=diaf_list[value]
        inst_dir=os.path.dirname(__file__)
        abs_path=os.path.join(inst_dir, 'diafs_settings.json')
        with open(abs_path) as savfile:
            data=json.load(savfile) #data is load json
        if which=='ROA':
            self.m1_f=data[which][value]['m1']
            self.m2_f=data[which][value]['m2']
        elif which=='VOA':
            self.m3_f=data[which][value]['m3']
            self.m4_f=data[which][value]['m4']


    @property
    def voa_change_f(self):
        return self.__voa
		
    @voa_change_f.setter
    def voa_change_f(self, value):
        self.set_full_range.fire() #before change you need to let slider go anywhere so you can set the value
        self.__voa=value
        self.set_values(value, 'VOA')
        self.property_changed_event.fire('voa_change_f')
		
    @property
    def roa_change_f(self):
        return self.__roa
		
    @roa_change_f.setter
    def roa_change_f(self, value):
        self.set_full_range.fire() #before change you need to let slider go anywhere so you can set the value
        self.__roa=value
        self.set_values(value, 'ROA')
        self.property_changed_event.fire('roa_change_f')


    @property
    def m1_f(self):
        return self.__m1
		
    @m1_f.setter
    def m1_f(self, value):
        self.__m1=value
        self.__apert.set_val(1, value)
        self.property_changed_event.fire('m1_f')	

    @property
    def m2_f(self):
        return self.__m2
		
    @m2_f.setter
    def m2_f(self, value):
        self.__m2=value
        self.__apert.set_val(2, value)
        self.property_changed_event.fire('m2_f')

    @property
    def m3_f(self):
        return self.__m3
		
    @m3_f.setter
    def m3_f(self, value):
        self.__m3=value
        self.__apert.set_val(3, value)
        self.property_changed_event.fire('m3_f')
			
    @property
    def m4_f(self):
        return self.__m4
		
    @m4_f.setter
    def m4_f(self, value):
        self.__m4=value
        self.__apert.set_val(4, value)
        self.property_changed_event.fire('m4_f')
