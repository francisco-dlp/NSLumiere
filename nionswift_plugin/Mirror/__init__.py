try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["mirror"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.instrumentation import HardwareSource
    from . import mirror_inst
    from . import mirror_panel
    def run():
        simpleInstrument=mirror_inst.mirrorDevice()
        HardwareSource.HardwareSourceManager().register_instrument("mirror_controller", simpleInstrument)
        mirror_panel.run(simpleInstrument)