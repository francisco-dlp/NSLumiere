# standard libraries
import json
import logging
import os
import sys
from pathlib import Path
import shutil

from nion.utils import Event
from nion.utils import Observable
from ..aux_files import read_data

set_file = read_data.FileManager('global_settings')
DEBUG = set_file.settings["stage"]["DEBUG"]

if DEBUG:
    from . import VGStage_vi as stage
else:
    from . import VGStage as stage

class stageDevice(Observable.Observable):
    def __init__(self):
        try:
            logging.info(f'***VG STAGE***: Placing Stepper.dll in {sys.executable}.')
            dll_path = os.path.join(os.path.dirname(__file__), '../aux_files/DLLs/Stepper.dll')
            parent_exec = os.path.join(Path(sys.executable).parent.absolute(), 'Stepper.dll')
            shutil.copyfile(dll_path, parent_exec)

            logging.info(f'***VG STAGE***: Placing delib64.dll in {sys.executable}.')
            dll_path = os.path.join(os.path.dirname(__file__), '../aux_files/DLLs/delib64.dll')
            parent_exec = os.path.join(Path(sys.executable).parent.absolute(), 'delib64.dll')
            shutil.copyfile(dll_path, parent_exec)
        except PermissionError:
            logging.info(f'***VG STAGE***: Error in installing DLLs. Please make sure they are in the correct path before running.')

        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__data = read_data.FileManager("stage_settings")
        self.__sendmessage = stage.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__vgStage=stage.VGStage(self.__sendmessage)

        self.__x, self.__y = self.__vgStage.stageGetPosition()
        self.__text = self.__data.settings['text']

    def save_values(self, string):
        self.__data.settings['text'] = string
        self.__data.settings['pos']['x'] = self.__x
        self.__data.settings['pos']['x'] = self.__y
        self.__data.save_locally()

    def GetPos(self):
        return self.__vgStage.stageGetPosition()

    def set_origin(self):
        self.__vgStage.stageInit(True, True, True)

    def free_UI(self, *args):
        for arg in args:
            if arg=='x':
                self.property_changed_event.fire('x_pos_f')
                self.property_changed_event.fire('x_pos_edit_f')
            elif arg=='y':
                self.property_changed_event.fire('y_pos_f')
                self.property_changed_event.fire('y_pos_edit_f')

    def busy_UI(self, *args):
        for arg in args:
            self.busy_event.fire(arg)

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG STAGE***: VG Stage not found. Please check if its connected and if STEMSerial.dll is present at the same folder as the installation. Also make sure Stepper.dll is inside your python folder.")
            if message == 2:
                logging.info("***VG STAGE***: Attempt to input a value out of boundary. Please if the value makes sense check VG Stage origin.")

        return sendMessage

    @property
    def x_pos_edit_f(self):
        return '{:.2f}'.format(self.__x*1e6)

    @x_pos_edit_f.setter
    def x_pos_edit_f(self, value):
        self.__x = float(value)/1e6
        self.__vgStage.stageGoTo_x(self.__x)
        self.property_changed_event.fire('x_pos_edit_f')

    @property
    def y_pos_edit_f(self):
        return '{:.2f}'.format(self.__y*1e6)

    @y_pos_edit_f.setter
    def y_pos_edit_f(self, value):
        self.__y = float(value)/1e6
        self.__vgStage.stageGoTo_y(self.__y)
        self.property_changed_event.fire('y_pos_edit_f')

    @property
    def text_f(self):
        return self.__text

    @text_f.setter
    def text_f(self, value):
        self.__text = value
        self.save_values(value)