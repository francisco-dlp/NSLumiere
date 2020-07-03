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

DEBUG = 1

if DEBUG:
    from . import VGStage_vi as stage
else:
    from . import VGStage as stage



class stageDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        
        self.__sendmessage = stage.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__vgStage=stage.VGStage(self.__sendmessage)

        #Stepper DLL should be here
        #You need to have STEMSerial.dll and put Stepper.dll in python folder

        self.__x, self.__y = self.__vgStage.stageGetPosition()


    def GetPos(self):
        return self.__vgStage.stageGetPosition()

    def set_origin(self):
        #self.__vgStage.stageInit(True, True, True)
        logging.info('Disabled for now. X switch seems to be malfunctioning')

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG STAGE***: VG Stage not found. Please check if its connected and if STEMSerial.dll is present at the same folder as the installation. Also make sure Stepper.dll is inside your python folder.")
            if message == 2:
                logging.info("***VG STAGE***: Attempt to input a value out of boundary. Please if the value makes sense check VG Stage origin.")

        return sendMessage


    @property
    def x_pos_f(self):
        return int(self.__x*1e6)

    @x_pos_f.setter
    def x_pos_f(self, value):
        self.__x=value/1e6
        self.__vgStage.stageGoTo_x(self.__x)
        self.property_changed_event.fire('x_pos_f')
        self.property_changed_event.fire('x_pos_edit_f')

    @property
    def x_pos_edit_f(self):
        return '{:.2f}'.format(self.__x*1e6)

    @x_pos_edit_f.setter
    def x_pos_edit_f(self, value):
        self.__x = float(value)/1e6
        self.__vgStage.stageGoTo_x(self.__x)
        self.property_changed_event.fire('x_pos_f')
        self.property_changed_event.fire('x_pos_edit_f')

    @property
    def y_pos_f(self):
        return int(self.__y*1e6)

    @y_pos_f.setter
    def y_pos_f(self, value):
        self.__y = value/1e6
        self.__vgStage.stageGoTo_y(self.__y)
        self.property_changed_event.fire('y_pos_f')
        self.property_changed_event.fire('y_pos_edit_f')

    @property
    def y_pos_edit_f(self):
        return '{:.2f}'.format(self.__y*1e6)

    @y_pos_edit_f.setter
    def y_pos_edit_f(self, value):
        self.__y = float(value)/1e6
        self.__vgStage.stageGoTo_y(self.__y)
        self.property_changed_event.fire('y_pos_f')
        self.property_changed_event.fire('y_pos_edit_f')
