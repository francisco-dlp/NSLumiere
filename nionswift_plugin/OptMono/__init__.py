from nion.swift.model import HardwareSource

from . import mono_inst
from . import mono_panel


def run():

    simpleInstrument=mono_inst.MonoDevice()
    HardwareSource.HardwareSourceManager().register_instrument("mono_controller", simpleInstrument)
    mono_panel.run(simpleInstrument)


