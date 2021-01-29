from nion.swift.model import HardwareSource


import logging
from . import eels_spec_inst
from . import eels_spec_panel



number = 12
names = ['fx', 'fy', 'sx', 'sy', 'dy', 'q1', 'q2', 'q3', 'q4', 'dx', 'dmx', 'off']

def run():

    simpleInstrument=eels_spec_inst.EELS_SPEC_Device(nElem = 12, ElemNames = names)
    HardwareSource.HardwareSourceManager().register_instrument("eels_spec_controller", simpleInstrument)
    eels_spec_panel.run(simpleInstrument)


