# standard libraries
import os
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

from . import lens_ps as lens_ps

class probeDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        #self.property_changed_event_listener = self.property_changed_event.listen(self.computeCalibration)
        self.busy_event=Event.Event()
        

			
		
        self.__sendmessage = lens_ps.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__lenses_ps = lens_ps.Lenses(self.__sendmessage)
		
		
        self.__obj=0.
        self.__obj_global=True
		
        self.__c1=0.
        self.__c1_global=True
		
        self.__c2=0.
        self.__c2_global=True		
		
        try:
            inst_dir=os.path.dirname(__file__)
            abs_path=os.path.join(inst_dir, 'lenses_settings.txt')
            savfile=open(abs_path, 'r')
            values=savfile.readlines() 
            self.obj_edit_f=float((values[0])[4:])
            self.c1_edit_f=float((values[1])[4:])
            self.c2_edit_f=float((values[2])[4:])
        except:
            logging.info('***LENS***: No saved values.')


    def sendMessageFactory(self):
        def sendMessage(message):
            if message==1:
                logging.info("Could not find Lenses PS")

        return sendMessage


### OBJ ###

    @property
    def obj_global_f(self):
        return self.__obj_global
		
    @obj_global_f.setter
    def obj_global_f(self, value):
        if value:
            self.__lenses_ps.set_val(self.__obj, 'OBJ')
        else:
            self.__lenses_ps.set_val(0.0, 'OBJ')

    @property
    def obj_slider_f(self):
        return int(self.__obj*1e6)
		
    @obj_slider_f.setter
    def obj_slider_f(self, value):
        self.__obj=value/1e6
        self.__lenses_ps.set_val(self.__obj, 'OBJ')
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")
		
    @property
    def obj_edit_f(self):
        return format(self.__obj, '.6f')
		
    @obj_edit_f.setter
    def obj_edit_f(self, value):
        self.__obj=float(value)
        self.__lenses_ps.set_val(self.__obj, 'OBJ')
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")
		
### C1 ###

    @property
    def c1_global_f(self):
        return self.__c1_global
		
    @c1_global_f.setter
    def c1_global_f(self, value):
        if value:
            self.__lenses_ps.set_val(self.__c1, 'C1')
        else:
            self.__lenses_ps.set_val(0.0, 'C1')
		
    @property
    def c1_slider_f(self):
        return int(self.__c1*1e6)
		
    @c1_slider_f.setter
    def c1_slider_f(self, value):
        self.__c1=value/1e6
        self.__lenses_ps.set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")
		
    @property
    def c1_edit_f(self):
        return format(self.__c1, '.6f')
		
    @c1_edit_f.setter
    def c1_edit_f(self, value):
        self.__c1=float(value)
        self.__lenses_ps.set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")
	
### C2 ###

    @property
    def c2_global_f(self):
        return self.__c2_global
		
    @c2_global_f.setter
    def c2_global_f(self, value):
        if value:
            self.__lenses_ps.set_val(self.__c2, 'C2')
        else:
            self.__lenses_ps.set_val(0.0, 'C2')
		
    @property
    def c2_slider_f(self):
        return int(self.__c2*1e6)
		
    @c2_slider_f.setter
    def c2_slider_f(self, value):
        self.__c2=value/1e6
        self.__lenses_ps.set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")
		
    @property
    def c2_edit_f(self):
        return format(self.__c2, '.6f')
		
    @c2_edit_f.setter
    def c2_edit_f(self, value):
        self.__c2=float(value)
        self.__lenses_ps.set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")