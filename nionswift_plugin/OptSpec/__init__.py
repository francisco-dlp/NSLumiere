from nion.swift.model import HardwareSource

from . import optspec_inst
from . import optspec_panel

import os
import json

try:
    abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
    with open(abs_path) as savfile:
        settings = json.load(savfile)
    DEBUG = settings["SPECTROMETER"]["DEBUG"]
    MANUFACTURER = settings["SPECTROMETER"]["MANUFACTURER"]
except KeyError:
    DEBUG = False
    MANUFACTURER = ["ATTOLIGHT"]

for MAN in MANUFACTURER:
    def run():
        simpleInstrument=optspec_inst.OptSpecDevice(MAN)
        HardwareSource.HardwareSourceManager().register_instrument("_optSpec_controller", simpleInstrument)
        optspec_panel.run(simpleInstrument)


