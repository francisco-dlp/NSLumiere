import logging
from nion.utils import Registry

from . import ivg_inst
from . import ivg_panel
from . import ivg_spim_panel

from .camera import VGCameraPanel, VGCameraYves
try:
    from .scan import VGScanYves
except ModuleNotFoundError:
    logging.info("***IVG***: SCAN Module not found. If this is unintended please add it"
                 "in the setup file.")

IMPORT_VG_SCAN = True

def run():
    instrument = ivg_inst.ivgInstrument('VG_controller')
    # You definitely need to register the instrument over here.
    Registry.register_component(instrument, {"instrument_controller", "stem_controller"})

    ivg_panel.run(instrument)
    #ivg_spim_panel.run(instrument)
    try:
        if IMPORT_VG_SCAN:
            VGScanYves.run(instrument)
        else:
            logging.info("***IVG***: Skipping VGScan. Please check the init file.")
    except NameError:
        logging.info("***IVG***: Skipping VGScan. Module not imported.")
    VGCameraYves.run(instrument)
    VGCameraPanel.run()