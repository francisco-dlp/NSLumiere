from nion.utils import Registry

from . import ivg_inst
from . import ivg_panel
from . import ivg_spim_panel

from .camera import VGCameraPanel, VGCameraYves
from .scan import VGScanYves

def run():

    instrument = ivg_inst.ivgInstrument('VG_Lum_controller')
    # You definitely need to register the instrument over here.
    Registry.register_component(instrument, {"instrument_controller", "stem_controller"})

    ivg_panel.run(instrument)
    ivg_spim_panel.run(instrument)
    #VGScanYves.run(instrument)
    VGCameraYves.run(instrument)
    VGCameraPanel.run()

