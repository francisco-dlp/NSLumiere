try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["lenses"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.instrumentation import HardwareSource
    from . import probe_inst
    from . import probe_panel
    def run():
        simpleInstrument=probe_inst.probeDevice()
        HardwareSource.HardwareSourceManager().register_instrument("lenses_controller", simpleInstrument)
        probe_panel.run(simpleInstrument)