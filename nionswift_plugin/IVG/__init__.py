from nion.utils import Registry
import os
import json

abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/global_settings.json')
with open(abs_path) as savfile:
    settings = json.load(savfile)

DEBUG_CAMERA = settings["IVG"]["CAMERA"]["DEBUG"]
DEBUG_SCAN = settings["IVG"]["DEBUG_SCAN"]

from . import ivg_inst
from . import ivg_panel
from . import ivg_spim_panel
from .tp3 import tp3_camera, tp3_aux_panel

from .camera import VGCameraPanel, VGCameraYves
if not DEBUG_SCAN:
    from .scan import VGScanYves

def run():

    instrument = ivg_inst.ivgInstrument('VG_Lum_controller')
    # You definitely need to register the instrument over here.
    Registry.register_component(instrument, {"instrument_controller", "stem_controller"})

    ivg_panel.run(instrument)
    if not DEBUG_CAMERA and not DEBUG_SCAN: ivg_spim_panel.run(instrument)
    if not DEBUG_SCAN: VGScanYves.run(instrument)
    if not DEBUG_CAMERA:
        VGCameraYves.run(instrument)
        VGCameraPanel.run()

