try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
ACTIVATED = set_file.settings["EELS"]["ACTIVATED"]
if bool(ACTIVATED):
    from nion.utils import Registry

    from . import eels_spec_inst
    from . import eels_spec_panel
    names = ['fx', 'fy', 'sx', 'sy', 'dy', 'q1', 'q2', 'q3', 'q4', 'dx', 'dmx', 'off',
             'binding', 'binding_offset_dm', 'binding_offset_dmx']
    def run():
        simpleInstrument=eels_spec_inst.EELS_SPEC_Device(nElem=len(names), ElemNames=names)
        Registry.register_component(simpleInstrument, {"eels_spec_controller"})
        eels_spec_panel.run(simpleInstrument)