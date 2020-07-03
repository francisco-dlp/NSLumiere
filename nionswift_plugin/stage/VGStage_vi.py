"""
# -*- coding:utf-8 -*-
Class wrapping the Marcel Tencé dll for controlling a stage.
"""

from nion.utils import Event

__author__ = "Marcel Tence & Mathieu Kociak & Yves Auad"


def _isPython3():
    return sys.version_info[0] >= 3

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class VGStage(object):

    def __init__(self, sendmessage):
        self.__x_pos = 0.
        self.__y_pos = 0.
        self.sendmessage = sendmessage




    def stageInit(self, x_axis: bool, y_axis: bool, always: bool):
        pass

    def stageCancelInit(self, axis: int):
        pass

    def stageGetPosition(self):
        return self.__x_pos, self.__y_pos

    def stageGetSwitches(self, axis: int):
        pass

    def stageGetPositionAndSwitches(self):
        pass

    def stageGoTo(self, x: float, y: float):
        if abs(x)<1e-3 and abs(y)<1e-3:
            self.__x_pos=x
            self.__y_pos=y
        else:
            self.sendmessage(2)

    def stageGoTo_x(self, x):
        if abs(x)<1e-3:
            self.__x_pos = x
        else:
            self.sendmessage(2)

    def stageGoTo_y(self, y):
        if abs(y)<1e-3:
            self.__y_pos = y
        else:
            self.sendmessage(2)
