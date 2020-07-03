"""
# -*- coding:utf-8 -*-
Class wrapping the Marcel Tencé dll for controlling a stage.
"""
import sys
from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_short, c_int, c_long, c_bool, c_double, c_uint64, \
    c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
import os

from nion.utils import Event

__author__ = "Marcel Tence & Mathieu Kociak & Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3


def _buildFunction(call, args, result):
    call.argtypes = args
    call.restype = result
    return call


def _createCharBuffer23(size):
    if (_isPython3()):
        return create_string_buffer(b'\000' * size)
    return create_string_buffer('\000' * size)


def _convertToString23(binaryString):
    if (_isPython3()):
        return binaryString.decode("utf-8")
    return binaryString


def _toString23(string):
    if (_isPython3()):
        return string.encode("utf-8")
    return string


# is64bit = sys.maxsize > 2**32
if (sys.maxsize > 2 ** 32):
    libname = os.path.dirname(__file__)
    libname = os.path.join(libname, "STEMSerial.dll")
    _library = cdll.LoadLibrary(libname)
    print("Orsay STEMSerial library: ", _library)
else:
    raise Exception("It must a python 64 bit version")

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc



LOGGERFUNC = WINFUNCTYPE(None, c_char_p)
MOTOR = WINFUNCTYPE(c_void_p)

# void VG_EXPORT *OrsayStageInit();
_OrsayStageInit = _buildFunction(_library.OrsayStageInit, None, c_void_p)

# void VG_EXPORT OrsayStageClose(void *o);
_OrsayStageClose = _buildFunction(_library.OrsayStageClose, [c_void_p], None)

# void VG_EXPORT Initialisation(void *o, short motor, bool always);
_OrsayStageInitialise = _buildFunction(_library.Initialise, [c_void_p, c_short, c_bool], None)
# void VG_EXPORT CancelInitialisation(void *o, short motor);
_OrsayStageCancelInitialisation = _buildFunction(_library.CancelInitialisation, [c_void_p, c_short], None)
# short VG_EXPORT IsInitialised(void *o, short motor);
_OrsayStageIsInitialised = _buildFunction(_library.IsInitialised, [c_void_p, c_short], c_short)

# long VG_EXPORT MotorGetCalStatus(void *o, short motor, double *pos, short *swdebut, short *swmilieu, short *swfin);
_OrsayStageMotorGetCalStatus = _buildFunction(_library.MotorGetCalStatus,
                                              [c_void_p, c_short, POINTER(c_double), POINTER(c_short), POINTER(c_short),
                                               POINTER(c_short)], c_long)
# long VG_EXPORT MotorGoToCalPosition(void *o, short motor, double val);
_OrsayStageMotorGoToCalPosition = _buildFunction(_library.MotorGoToCalPosition, [c_void_p, c_short, c_double], c_long)


class VGStage(object):

    def __logger(self, message):
        """ Permet de capter les messages de la dll"""
        print("log: ", _convertToString23(message))

    def __init__(self, fn=None):
        """ Instancie la dll
        fn callback pour logger les messages (pourrait sans doute être self.__logger)
        """
        if fn is None:
            self.__logger_func = LOGGERFUNC(self.__logger)
        else:
            self.__logger_func = fn

        self._InitOk = False
        try:
            self._stage = _OrsayStageInit()
            if not self._stage:
                self.sendmessage(1)
            self._InitOk = _OrsayStageIsInitialised(self._stage, 0)
        except:
            pass

    def close(self):
        """ ferme la dll """
        if self.__property_changed_event_listener is not None:
            self.__property_changed_event_listener.close()
        self.__property_changed_event_listener = None
        _OrsayStageClose(self._stage)
        self._stage = 0


    def stageInit(self, x_axis: bool, y_axis: bool, always: bool):
        """ lance la recherche de l'origine pour un ou deux axes
        always est vrai: elle est toujours faite
        est faux: n'est pas fait quand on sait que l'initialisation a déjà été faite
        l'intérêt de forcer permet de corriger l'axe si on a perdu des pas !
        """
        if (x_axis):
            _OrsayStageInitialise(self._stage, 0, always)
        if (y_axis):
            _OrsayStageInitialise(self._stage, 1, always)

    def stageCancelInit(self, axis: int):
        """ arrête l'initialisation en cours """
        if (axis == 0) or (axis == -1):
            _OrsayStageCancelInitialisation(self._stage, 0)
        if (axis == 1) or (axis == -1):
            _OrsayStageCancelInitialisation(self._stage, 1)

    def stageGetPosition(self):
        """ lit la position actuelle de la platine """
        pos, swdebut, swmilieu, swfin = c_double(), c_short(), c_short(), c_short()
        _OrsayStageMotorGetCalStatus(self._stage, 0, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        xpos = pos.value
        _OrsayStageMotorGetCalStatus(self._stage, 1, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        ypos = pos.value
        return xpos, ypos

    def stageGetSwitches(self, axis: int):
        """ lit l'état des swicths de la platine """
        pos, swdebut, swmilieu, swfin = c_double(), c_short(), c_short(), c_short()
        if (axis == 0):
            _OrsayStageMotorGetCalStatus(self._stage, 0, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        if (axis == 1):
            _OrsayStageMotorGetCalStatus(self._stage, 1, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        return swdebut.value != 0, swmilieu.value != 0, swfin.value != 0

    def stageGetPositionAndSwitches(self):
        """ lit la position actuelle de la platine et l'état des switchs"""
        pos, swdebut, swmilieu, swfin = c_double(), c_short(), c_short(), c_short()
        _OrsayStageMotorGetCalStatus(self._stage, 0, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        xpos = (pos.value, swdebut.value != 0, swmilieu.value != 0, swfin.value != 0)
        _OrsayStageMotorGetCalStatus(self._stage, 1, byref(pos), byref(swdebut), byref(swmilieu), byref(swfin))
        ypos = (pos.value, swdebut.value != 0, swmilieu.value != 0, swfin.value != 0)
        return xpos, ypos

    def stageGoTo(self, x: float, y: float):
        """ Va à la position demandée [x, y] """
        if abs(x)<1e-3 and abs(y)<1e-3:
            _OrsayStageMotorGoToCalPosition(self._stage, 0, x)
            _OrsayStageMotorGoToCalPosition(self._stage, 1, y)
        else:
            self.sendmessage(2)

    def stageGoTo_x(self, x):
        if abs(x)<1e-3:
            _OrsayStageMotorGoToCalPosition(self._stage, 0, x)
        else:
            self.sendmessage(2)

    def stageGoTo_y(self, y):
        if abs(y)<1e-3:
            _OrsayStageMotorGoToCalPosition(self._stage, 1, y)
        else:
            self.sendmessage(2)
