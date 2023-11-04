from . import optspec_inst, optspec_panel
try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

from nion.utils import Registry
set_file = read_data.FileManager('global_settings')
MANUFACTURER = set_file.settings["spectrometer"]["WHICH"]

def run():
    for MAN in MANUFACTURER:
        simpleInstrument= optspec_inst.OptSpecDevice(MAN)
        Registry.register_component(simpleInstrument, {"optSpec_controller "+MAN})
        optspec_panel.run(simpleInstrument, 'Optical Spectrometer ' + MAN)