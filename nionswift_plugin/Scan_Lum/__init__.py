from nion.swift.model import HardwareSource


import logging
from . import scan_inst
from . import scan_panel


def run():

    simpleInstrument=scan_inst.scanDevice()
    HardwareSource.HardwareSourceManager().register_instrument("scan_controller", simpleInstrument)
    scan_panel.run(simpleInstrument)


