#from nion.swift.model import HardwareSource
from nion.instrumentation import HardwareSource


import logging
from . import diaf_inst
from . import diaf_panel


def run():

    simpleInstrument=diaf_inst.diafDevice()
    HardwareSource.HardwareSourceManager().register_instrument("diaf_controller", simpleInstrument)
    diaf_panel.run(simpleInstrument)


