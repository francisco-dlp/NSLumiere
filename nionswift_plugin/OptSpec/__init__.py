from nion.swift.model import HardwareSource
from . import optspec_inst, optspec_panel
import os, json

abs_path = os.path.abspath('C:\ProgramData\Microscope\global_settings.json')
try:
    with open(abs_path) as savfile:
        settings = json.load(savfile)
except FileNotFoundError:
    abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/global_settings.json')
    with open(abs_path) as savfile:
        settings = json.load(savfile)

MANUFACTURER = settings["spectrometer"]["WHICH"]

def run():
    for MAN in MANUFACTURER:
        simpleInstrument= optspec_inst.OptSpecDevice(MAN)
        HardwareSource.HardwareSourceManager().register_instrument("optSpec_controller "+MAN, simpleInstrument)
        optspec_panel.run(simpleInstrument, 'Optical Spectrometer ' + MAN)