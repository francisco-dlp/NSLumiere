from nion.swift.model import HardwareSource


import logging
from . import probe_inst
from . import probe_panel

names = ['obj', 'c1', 'c2']

def run():

    simpleInstrument=probe_inst.probeDevice(nLens=3, LensNames=names)
    HardwareSource.HardwareSourceManager().register_instrument("lenses_controller", simpleInstrument)
    probe_panel.run(simpleInstrument)


