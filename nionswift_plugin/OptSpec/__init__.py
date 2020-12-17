from nion.swift.model import HardwareSource

from . import optspec_inst
from . import optspec_panel

def run():
    simpleInstrument=optspec_inst.OptSpecDevice()
    HardwareSource.HardwareSourceManager().register_instrument("optSpec_controller", simpleInstrument)
    optspec_panel.run(simpleInstrument)


