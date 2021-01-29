from nion.swift.model import HardwareSource


import logging
from . import probe_inst
from . import probe_panel

names = ['obj', 'c1', 'c2']
stignames = ['obj_stig_00', 'obj_stig_01', 'gun_stig_02', 'gun_stig_03']

def run():

    simpleInstrument=probe_inst.probeDevice(nLens=3, LensNames=names, nStig=4, StigNames = stignames)
    HardwareSource.HardwareSourceManager().register_instrument("lenses_controller", simpleInstrument)
    probe_panel.run(simpleInstrument)


