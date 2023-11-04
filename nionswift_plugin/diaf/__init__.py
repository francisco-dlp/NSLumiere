try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["diaf"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.utils import Registry
    from . import diaf_inst
    from . import diaf_panel
    def run():
        simpleInstrument=diaf_inst.diafDevice()
        Registry.register_component(simpleInstrument, {"diaf_controller"})
        diaf_panel.run(simpleInstrument)