from nion.swift.model import HardwareSource

from . import optspec_inst, optspec_panel

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
except FileNotFoundError:
    DEBUG = False
    MANUFACTURER = ["DEBUG", "ATTOLIGHT", "PRINCETON"]

def run():
    for MAN in MANUFACTURER:
        simpleInstrument= optspec_inst.OptSpecDevice(MAN)
        HardwareSource.HardwareSourceManager().register_instrument("optSpec_controller "+MAN, simpleInstrument)
        optspec_panel.run(simpleInstrument, 'Optical Spectrometer ' + MAN)


