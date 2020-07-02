from nion.swift.model import HardwareSource


import logging
from . import stage_inst
from . import stage_panel


def run():

    simpleInstrument=stage_inst.stageDevice()
    HardwareSource.HardwareSourceManager().register_instrument("stage_controller", simpleInstrument)
    stage_panel.run(simpleInstrument)


