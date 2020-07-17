from nion.utils import Registry

import logging
from . import ivg_inst
from . import ivg_panel
from . import VGScanYves
from . import VGCameraYves
from . import VGCameraPanel


def run():

    instrument = ivg_inst.ivgInstrument('VG_Lum_controller')
    Registry.register_component(instrument, {"instrument_controller", "stem_controller"})

    ivg_panel.run(instrument)
    VGScanYves.run(instrument)
    VGCameraYves.run(instrument)
    VGCameraPanel.run()
