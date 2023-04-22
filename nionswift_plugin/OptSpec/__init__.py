from nion.instrumentation import HardwareSource

from . import optspec_inst, optspec_panel
from ..aux_files import read_data

set_file = read_data.FileManager('global_settings')
MANUFACTURER = set_file.settings["spectrometer"]["WHICH"]

def run():
    for MAN in MANUFACTURER:
        simpleInstrument= optspec_inst.OptSpecDevice(MAN)
        HardwareSource.HardwareSourceManager().register_instrument("optSpec_controller "+MAN, simpleInstrument)
        optspec_panel.run(simpleInstrument, 'Optical Spectrometer ' + MAN)