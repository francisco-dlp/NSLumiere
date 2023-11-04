try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["EELS"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.instrumentation import HardwareSource
    from . import eels_spec_inst
    from . import eels_spec_panel
    number = 12
    names = ['fx', 'fy', 'sx', 'sy', 'dy', 'q1', 'q2', 'q3', 'q4', 'dx', 'dmx', 'off']
    def run():
        usim = HardwareSource.HardwareSourceManager().get_instrument_by_id("usim_stem_controller")
        simpleInstrument=eels_spec_inst.EELS_SPEC_Device(nElem=12, ElemNames=names)
        HardwareSource.HardwareSourceManager().register_instrument("eels_spec_controller", simpleInstrument)
        eels_spec_panel.run(simpleInstrument)