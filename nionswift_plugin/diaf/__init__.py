from nion.swift.model import HardwareSource

from . import diaf_inst
from . import diaf_panel

dict = {'ROA': ['None', '50', '100', '150'], 'VOA': ['None', '50', '100', '150']}

def run():

    simpleInstrument=diaf_inst.diafDevice(dict)
    HardwareSource.HardwareSourceManager().register_instrument("diaf_controller", simpleInstrument)
    diaf_panel.run(simpleInstrument)


