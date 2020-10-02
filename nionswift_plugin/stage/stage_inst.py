# standard libraries
import json
import logging
import os
import sys

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

DEBUG = settings["stage"]["DEBUG"]

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
        self.slider_event=Event.Event()
        
        self.__sendmessage = stage.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__vgStage=stage.VGStage(self.__sendmessage)

        self.__x, self.__y = self.__vgStage.stageGetPosition()
        self.__slider_range = 400

        logging.info(f'***VG STAGE***: Please put Stepper.dll at the following folder: {sys.executable}.')


    def GetPos(self):
        return self.__vgStage.stageGetPosition()

    def set_origin(self):
        #self.__vgStage.stageInit(True, True, True)
        logging.info('Disabled for now. X switch seems to be malfunctioning')

    def free_UI(self):
        self.property_changed_event.fire('x_pos_f')
        self.property_changed_event.fire('x_pos_edit_f')
        self.property_changed_event.fire('y_pos_f')
        self.property_changed_event.fire('y_pos_edit_f')

    def busy_UI(self):
        self.busy_event.fire('')

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG STAGE***: VG Stage not found. Please check if its connected and if STEMSerial.dll is present at the same folder as the installation. Also make sure Stepper.dll is inside your python folder.")
            if message == 2:
                logging.info("***VG STAGE***: Attempt to input a value out of boundary. Please if the value makes sense check VG Stage origin.")

        return sendMessage


    @property
    def x_pos_f(self):
        return int(self.__x*1e8)

    @x_pos_f.setter
    def x_pos_f(self, value):
        self.__x=value/1e8
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
        return int(self.__y*1e8)

    @y_pos_f.setter
    def y_pos_f(self, value):
        self.__y = value/1e8
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

    @property
    def slider_range_f(self):
        return self.__slider_range

    @slider_range_f.setter
    def slider_range_f(self, value):
        self.__slider_range=int(value*100)
        if self.__slider_range<32000:
            try:
                self.slider_event.fire()
            except:
                pass
        self.property_changed_event.fire('slider_range_f')

