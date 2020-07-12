from nion.swift.model import HardwareSource
from nion.utils import Registry

import logging
from . import ivg_inst
from . import ivg_panel
from . import VGScanYves
from . import VGCameraYves
from . import VGCameraPanel


def run():

    simpleInstrument=ivg_inst.ivgDevice()
    HardwareSource.HardwareSourceManager().register_instrument("Instrument_VG", simpleInstrument)
    ivg_panel.run(simpleInstrument)


    instrument = ivg_inst.ivgInstrument('VG_Lum_controller')
    Registry.register_component(instrument, {"instrument_controller", "stem_controller"})

    VGScanYves.run(instrument)
    VGCameraYves.run(instrument)
    VGCameraPanel.run()