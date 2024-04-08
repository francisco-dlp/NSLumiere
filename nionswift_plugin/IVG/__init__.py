try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ORSAY_SCAN_ACTIVATED = set_file.settings["OrsayInstrument"]["orsay_scan"]["ACTIVATED"]
IS_VG = set_file.settings["OrsayInstrument"]["orsay_scan"]["IS_VG"]
OPEN_SCAN_ACTIVATED = set_file.settings["OrsayInstrument"]["open_scan"]["ACTIVATED"]

from nion.utils import Registry
from . import ivg_inst, ivg_panel
from .camera import VGCameraPanel, VGCameraYves

def run():
    VGCameraYves.run()
    VGCameraPanel.run()

    if bool(ORSAY_SCAN_ACTIVATED) or bool(OPEN_SCAN_ACTIVATED):
        instrument = ivg_inst.ivgInstrument('orsay_controller', 25)
        Registry.register_component(instrument, {"instrument_controller", "stem_controller"})
    if bool(ORSAY_SCAN_ACTIVATED) and bool(OPEN_SCAN_ACTIVATED):
        instrument_2 = ivg_inst.ivgInstrument('orsay_controller_2', 20)
        Registry.register_component(instrument_2, {"instrument_controller", "stem_controller"})


    if bool(ORSAY_SCAN_ACTIVATED):
        from .scan import VGScanYves
        #If both scans are up, we set orsay_scan to instrument_2.
        if IS_VG:
            if bool(ORSAY_SCAN_ACTIVATED) and bool(OPEN_SCAN_ACTIVATED):
                ivg_panel.run(instrument_2)
            else:
                ivg_panel.run(instrument)
        if bool(ORSAY_SCAN_ACTIVATED) and bool(OPEN_SCAN_ACTIVATED):
            VGScanYves.run(instrument_2)
        else:
            VGScanYves.run(instrument)

    if bool(OPEN_SCAN_ACTIVATED):
        from .scan import OScanCesys
        if IS_VG:
            ivg_panel.run(instrument)
        OScanCesys.run(instrument)