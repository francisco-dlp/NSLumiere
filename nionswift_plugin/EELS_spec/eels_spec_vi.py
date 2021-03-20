from . import EELS_controller

__author__ = "Yves Auad"

class EELS_Spectrometer(EELS_controller.EELSController):

    def __init__(self):
        super().__init__()

    def set_val(self, val, which):
        if which=="vsm":
            pass
        else:
            if which == "dmx": which = "al"
            if abs(val)<32767:
                if val < 0:
                    val = abs(val)
                else:
                    val = 0xffff - val
                string = which+' 0,'+hex(val)[2:6]+'\r'
                return None
            else:
                self.sendmessage(3)