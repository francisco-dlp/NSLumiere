# standard libraries
import json
import os
import logging

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath('C:\ProgramData\Microscope\global_settings.json')
try:
    with open(abs_path) as savfile:
        settings = json.load(savfile)
except FileNotFoundError:
    abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
    with open(abs_path) as savfile:
        settings = json.load(savfile)

if "mirror" in settings:
    DEBUG = settings["mirror"]["DEBUG"]
    if DEBUG:
        from . import mirror_vi as mirror
    else:
        from . import mirror as mirror
else:
    from . import mirror_vi as mirror



class mirrorDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.set_full_range = Event.Event()

        self.__sendmessage = mirror.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__mir = mirror.Mirror(self.__sendmessage)

        self.__x = 0.
        self.__x_rel = 0.

        self.__y = 0.
        self.__y_rel = 0.

        self.__z = 0.
        self.__z_rel = 0.

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***MIRROR CONTROL***: Could not find mirror motor Hardware")
            if message == 2:
                logging.info("***MIRROR CONTROL***: Communication problem over serial port. Easy check using Serial Port Monitor.")

        return sendMessage


    @property
    def x_f(self):
        return self.__x

    @x_f.setter
    def x_f(self, value):
        self.__x = float(value)
        self.__mir.set_val(1, value)
        self.property_changed_event.fire('x_f')

    @property
    def x_rel_f(self):
        return self.__x_rel

    @x_rel_f.setter
    def x_rel_f(self, value):
        self.__x_rel = float(value)

    @property
    def y_f(self):
        return self.__y

    @y_f.setter
    def y_f(self, value):
        self.__y = float(value)
        self.__mir.set_val(2, value)
        self.property_changed_event.fire('y_f')

    @property
    def y_rel_f(self):
        return self.__y_rel

    @y_rel_f.setter
    def y_rel_f(self, value):
        self.__y_rel = float(value)

    @property
    def z_f(self):
        return self.__z

    @z_f.setter
    def z_f(self, value):
        self.__z = float(value)
        self.__mir.set_val(3, value)
        self.property_changed_event.fire('z_f')

    @property
    def z_rel_f(self):
        return self.__z_rel

    @z_rel_f.setter
    def z_rel_f(self, value):
        self.__z_rel = float(value)