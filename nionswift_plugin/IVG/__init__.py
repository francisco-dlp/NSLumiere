from nion.swift.model import HardwareSource


import logging
from . import ivg_inst
from . import ivg_panel


def run():

    simpleInstrument=ivg_inst.ivgDevice()
    HardwareSource.HardwareSourceManager().register_instrument("Instrument_VG", simpleInstrument)
    ivg_panel.run(simpleInstrument)


