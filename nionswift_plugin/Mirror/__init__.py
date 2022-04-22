#from nion.swift.model import HardwareSource
from nion.instrumentation import HardwareSource

from . import mirror_inst
from . import mirror_panel


def run():

    simpleInstrument=mirror_inst.mirrorDevice()
    HardwareSource.HardwareSourceManager().register_instrument("mirror_controller", simpleInstrument)
    mirror_panel.run(simpleInstrument)


