from nion.swift.model import HardwareSource
from . import optspec_inst, optspec_panel

MANUFACTURER = ["DEBUG", "ATTOLIGHT", "PRINCETON"]

def run():
    for MAN in MANUFACTURER:
        simpleInstrument= optspec_inst.OptSpecDevice(MAN)
        HardwareSource.HardwareSourceManager().register_instrument("optSpec_controller "+MAN, simpleInstrument)
        optspec_panel.run(simpleInstrument, 'Optical Spectrometer ' + MAN)