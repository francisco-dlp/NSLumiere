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

DEBUG = 0

if DEBUG:
    from . import stage_vi as stage
else:
    from . import stage as stage


class stageDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        # self.property_changed_event_listener = self.property_changed_event.listen(self.computeCalibration)
        self.busy_event = Event.Event()

        #self.__sendmessage = lens_ps.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        #self.__lenses_ps = lens_ps.Lenses(self.__sendmessage)

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***VG STAGE***: TEST")

        return sendMessage
