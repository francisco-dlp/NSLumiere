from nion.swift.model import HardwareSource


import logging
from . import eels_spec_inst
from . import eels_spec_panel


def run():

    simpleInstrument=eels_spec_inst.EELS_SPEC_Device()
    HardwareSource.HardwareSourceManager().register_instrument("eels_spec_controller", simpleInstrument)
    eels_spec_panel.run(simpleInstrument)


