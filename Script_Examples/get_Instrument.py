from nion.utils import Registry
from nion.swift.model import HardwareSource

my_insts = Registry.get_components_by_type("stem_controller")
for counter, my_inst in enumerate(list(my_insts)):
    print(my_inst.instrument_id)
    print(counter)

cams = dict()
scans = dict()

for hards in HardwareSource.HardwareSourceManager().hardware_sources:  # finding eels camera. If you don't
    if hasattr(hards, 'hardware_source_id'):
        if hasattr(hards, '_CameraHardwareSource__instrument_controller_id'):
            cams[hards.hardware_source_id]=hards._CameraHardwareSource__instrument_controller_id
        if hasattr(hards, '_ScanHardwareSource__stem_controller'):
            scans[hards.hardware_source_id]=hards._ScanHardwareSource__stem_controller.instrument_id

print('Cameras:')
print(cams)
print('Scans')
print(scans)