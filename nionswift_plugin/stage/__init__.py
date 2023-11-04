try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["stage"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.instrumentation import HardwareSource
    from . import stage_inst
    from . import stage_panel
    def run():
        simpleInstrument=stage_inst.stageDevice()
        HardwareSource.HardwareSourceManager().register_instrument("stage_controller", simpleInstrument)
        stage_panel.run(simpleInstrument)


