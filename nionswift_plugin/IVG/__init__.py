try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ORSAY_SCAN_ACTIVATED = set_file.settings["OrsayInstrument"]["orsay_scan"]["ACTIVATED"]
OPEN_SCAN_ACTIVATED = set_file.settings["OrsayInstrument"]["open_scan"]["ACTIVATED"]

import typing
from nion.utils import Registry
from . import ivg_inst, ivg_panel
from .camera import VGCameraPanel, VGCameraYves

def run():
    VGCameraYves.run()
    VGCameraPanel.run()

    if bool(OPEN_SCAN_ACTIVATED):
        from .scan import OScanCesys
        instrument2 = ivg_inst.ivgInstrument('orsay_controller2')
        Registry.register_component(instrument2, {"instrument_controller", "stem_controller"})
        OScanCesys.run(instrument2)

    if bool(ORSAY_SCAN_ACTIVATED):
        instrument = ivg_inst.ivgInstrument('orsay_controller')
        Registry.register_component(instrument, {"instrument_controller", "stem_controller"})
        ivg_panel.run(instrument)

        from .scan import VGScanYves
        VGScanYves.run(instrument)

    for component in Registry.get_components_by_type("scan_hardware_source"):
        scan_hardware_source = typing.cast("scan_base.ScanHardwareSource", component)
        if scan_hardware_source.hardware_source_id == "orsay_scan_device":
            instrument.set_scan_controller(scan_hardware_source)
        elif scan_hardware_source.hardware_source_id == "open_scan_device":
            instrument2.set_scan_controller(scan_hardware_source)