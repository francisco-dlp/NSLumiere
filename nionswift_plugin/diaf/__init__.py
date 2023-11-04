#from nion.swift.model import HardwareSource
try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["diaf"]["ACTIVATED"]
if bool(ACTIVATED):
    from . import diaf_inst
    from . import diaf_panel
    from nion.instrumentation import HardwareSource
    def run():
        simpleInstrument=diaf_inst.diafDevice()
        HardwareSource.HardwareSourceManager().register_instrument("diaf_controller", simpleInstrument)
        diaf_panel.run(simpleInstrument)