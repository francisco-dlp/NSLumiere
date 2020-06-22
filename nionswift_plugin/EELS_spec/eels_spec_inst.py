# standard libraries
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
    from . import eels_spec_vi as spec
else:
    from . import eels_spec as spec

class EELS_SPEC_Device(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        #self.property_changed_event_listener = self.property_changed_event.listen(self.computeCalibration)
        self.busy_event=Event.Event()
      
        self.__sendmessage = spec.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__eels_spec = spec.espec(self.__sendmessage)
	    
        self.__fx=0.
        self.__fy=0.
        self.__sx=0.
        self.__sy=0.
        self.__dy=0.
        self.__q1=0.
        self.__q2=0.
        self.__q3=0.
        self.__q4=0.
        self.__dx=0.
        self.__dmx=0.
		
        try:
            inst_dir=os.path.dirname(__file__)
            abs_path=os.path.join(inst_dir, 'eels_settings.txt')
            savfile=open(abs_path, 'r')
            values=savfile.readlines() 
            self.fx_edit_f=float((values[0])[4:])
            self.fy_edit_f=float((values[1])[4:])
            self.sx_edit_f=float((values[2])[4:])
            self.sy_edit_f=float((values[3])[4:])
            self.dy_edit_f=float((values[4])[4:])
            self.q1_edit_f=float((values[5])[4:])
            self.q2_edit_f=float((values[6])[4:])
            self.q3_edit_f=float((values[7])[4:])
            self.q4_edit_f=float((values[8])[4:])
            self.dx_edit_f=float((values[9])[4:])
            self.dmx_edit_f=float((values[10])[5:])
        except:
            logging.info('***EELS SPEC***: No saved values.')		
		



    def sendMessageFactory(self):
        def sendMessage(message):
            if message==1:
                logging.info("***EELS SPECTROMETER***: Could not find EELS Spec. Check Hardware")

        return sendMessage


### FX ###
    @property
    def fx_slider_f(self):
        return int(self.__fx)
		
    @fx_slider_f.setter
    def fx_slider_f(self, value):
        self.__fx=value
        self.__eels_spec.set_val(self.__fx, 'FX')
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")
		
    @property
    def fx_edit_f(self):
        return format(self.__fx, '.2f')
		
    @fx_edit_f.setter
    def fx_edit_f(self, value):
        self.__fx=float(value)
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")
		
### FY ###
    @property
    def fy_slider_f(self):
        return int(self.__fy)
		
    @fy_slider_f.setter
    def fy_slider_f(self, value):
        self.__fy=value
        self.__eels_spec.set_val(self.__fy, 'FY')
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")
		
    @property
    def fy_edit_f(self):
        return format(self.__fy, '.2f')
		
    @fy_edit_f.setter
    def fy_edit_f(self, value):
        self.__fy=float(value)
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")
		
### SX ###
    @property
    def sx_slider_f(self):
        return int(self.__sx)
		
    @sx_slider_f.setter
    def sx_slider_f(self, value):
        self.__sx=value
        self.__eels_spec.set_val(self.__sx, 'SX')
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")
		
    @property
    def sx_edit_f(self):
        return format(self.__sx, '.2f')
		
    @sx_edit_f.setter
    def sx_edit_f(self, value):
        self.__sx=float(value)
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")
		
### SY ###
    @property
    def sy_slider_f(self):
        return int(self.__sy)
		
    @sy_slider_f.setter
    def sy_slider_f(self, value):
        self.__sy=value
        self.__eels_spec.set_val(self.__sy, 'SY')
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")
		
    @property
    def sy_edit_f(self):
        return format(self.__sy, '.2f')
		
    @sy_edit_f.setter
    def sy_edit_f(self, value):
        self.__sy=float(value)
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")
		
### DY ###
    @property
    def dy_slider_f(self):
        return int(self.__dy)
		
    @dy_slider_f.setter
    def dy_slider_f(self, value):
        self.__dy=value
        self.__eels_spec.set_val(self.__dy, 'DY')
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")
		
    @property
    def dy_edit_f(self):
        return format(self.__dy, '.2f')
		
    @dy_edit_f.setter
    def dy_edit_f(self, value):
        self.__dy=float(value)
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")
		
### Q1 ###
    @property
    def q1_slider_f(self):
        return int(self.__q1)
		
    @q1_slider_f.setter
    def q1_slider_f(self, value):
        self.__q1=value
        self.__eels_spec.set_val(self.__q1, 'Q1')
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")
		
    @property
    def q1_edit_f(self):
        return format(self.__q1, '.2f')
		
    @q1_edit_f.setter
    def q1_edit_f(self, value):
        self.__q1=float(value)
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")	

### Q2 ###
    @property
    def q2_slider_f(self):
        return int(self.__q2)
		
    @q2_slider_f.setter
    def q2_slider_f(self, value):
        self.__q2=value
        self.__eels_spec.set_val(self.__q2, 'Q2')
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")
		
    @property
    def q2_edit_f(self):
        return format(self.__q2, '.2f')
		
    @q2_edit_f.setter
    def q2_edit_f(self, value):
        self.__q2=float(value)
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")	

### Q3 ###
    @property
    def q3_slider_f(self):
        return int(self.__q3)
		
    @q3_slider_f.setter
    def q3_slider_f(self, value):
        self.__q3=value
        self.__eels_spec.set_val(self.__q3, 'Q3')
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")
		
    @property
    def q3_edit_f(self):
        return format(self.__q3, '.2f')
		
    @q3_edit_f.setter
    def q3_edit_f(self, value):
        self.__q3=float(value)
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")	

### Q4 ###
    @property
    def q4_slider_f(self):
        return int(self.__q4)
		
    @q4_slider_f.setter
    def q4_slider_f(self, value):
        self.__q4=value
        self.__eels_spec.set_val(self.__q4, 'Q4')
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")
		
    @property
    def q4_edit_f(self):
        return format(self.__q4, '.2f')
		
    @q4_edit_f.setter
    def q4_edit_f(self, value):
        self.__q4=float(value)
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")	

### DX ###
    @property
    def dx_slider_f(self):
        return int(self.__dx)
		
    @dx_slider_f.setter
    def dx_slider_f(self, value):
        self.__dx=value
        self.__eels_spec.set_val(self.__dx, 'DX')
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")
		
    @property
    def dx_edit_f(self):
        return format(self.__dx, '.2f')
		
    @dx_edit_f.setter
    def dx_edit_f(self, value):
        self.__dx=float(value)
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")	

### DMX ###
    @property
    def dmx_slider_f(self):
        return int(self.__dmx)
		
    @dmx_slider_f.setter
    def dmx_slider_f(self, value):
        self.__dmx=value
        self.__eels_spec.set_val(self.__dmx, 'DMX')
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")
		
    @property
    def dmx_edit_f(self):
        return format(self.__dmx, '.2f')
		
    @dmx_edit_f.setter
    def dmx_edit_f(self, value):
        self.__dmx=float(value)
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")	
						
								
