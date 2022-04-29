from nion.instrumentation import HardwareSource

from . import probe_inst
from . import probe_panel

def run():
    simpleInstrument=probe_inst.probeDevice()
    HardwareSource.HardwareSourceManager().register_instrument("lenses_controller", simpleInstrument)
    probe_panel.run(simpleInstrument)


