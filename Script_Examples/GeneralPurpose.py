from nion.instrumentation import HardwareSource
from nion.utils import Registry

from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API

cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
open_scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("open_scan_device")
superscan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("superscan")
usim = HardwareSource.HardwareSourceManager().get_instrument_by_id("usim_stem_controller")
stage = Registry.get_component("stage_controller")
diaf = Registry.get_component("diaf_controller")
eels = Registry.get_component("eels_spec_controller")
orsay_controller = HardwareSource.HardwareSourceManager().get_instrument_by_id("orsay_controller")
main_controller = Registry.get_component("stem_controller")
all = HardwareSource.HardwareSourceManager().get_all_instrument_ids()


print(main_controller)
print(main_controller.scan_controller)
print(main_controller.scan_controller.scan_device.current_frame_parameters.subscan_pixel_size)
print(main_controller.scan_controller.scan_device.current_frame_parameters.as_dict())
print(main_controller.scan_controller.scan_device.scan_device_id)
#print(dir(main_controller.scan_controller.scan_device))
#print(dir(main_controller.scan_controller))
print(main_controller.scan_controller.scan_device.is_scanning)
#
# print("GETTING SUPERSCAN AND IT AS THE SCAN CONTROLLER OF THE AUTOSTEM OBJECT")
# superscan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("superscan")
# main_controller.set_scan_controller(superscan)
#
# print("NOW EVERYTHING WORKS")

#for component in Registry.get_components_by_type("scan_hardware_source"):
#    print(f'{component.hardware_source_id}: {component.scan_device.scan_device_is_secondary=}')

for component in Registry.get_components_by_type("scan_hardware_source"):
    print(component.hardware_source_id)
    print(component.scan_device.scan_device_is_secondary)
#            scan_hardware_source = typing.cast("scan_base.ScanHardwareSource", component)
            #if not scan_hardware_source.scan_device.scan_device_is_secondary:
#                return scan_hardware_source
#print(scan_hardware_source)

#print(main_controller.scan_controller.hardware_source_id)

#Acessing the DEBUG_IO in OpenScan
#probe_pos = open_scan.scan_device.scan_engine.debug_io.probe_offset

#print(superscan.is_playing)

#print(dir(cam.camera))
#cam.camera.camera.resumeSpim(4)

#print(eels)
#print(eels2)
#print(all)
#print(usim)

#scan.scan_device.orsayscan.SetBottomBlanking(0, 14, beamontime=1e-6, delay=500e-9)
#scan.scan_device.orsayscan.SetBottomBlanking(3, 14, risingedge=True, beamontime=10e-6, delay=500e-9)
#scan.scan_device.orsayscan.SetTdcLine(0, 2, 8 + 7)  #When width increases, this goes to higher values
#scan.scan_device.orsayscan.SetTdcLine(0, 2, 8 + 6)  #When width increases, this goes to smaller values
#scan.scan_device.orsayscan.SetTdcLine(0, 2, 8 + 5)  #Laser. This is delay dependent, so not so good

#scan.scan_device.orsayscan.AlObjective(0.1, 0, 0, 0)

#fov = scan.scan_device.field_of_view
#time_us = scan.scan_device.current_frame_parameters['pixel_time_us']
#ia = scan.scan_device.Image_area
#texp = cam.get_current_frame_parameters()['exposure_ms']/1000.
#cam_fp = cam.get_current_frame_parameters()['acquisition_mode']

#print(time_us)
#scan.start_playing()
#im = scan.grab_next_to_start()
#scan.abort_playing()

#data = cam.grab_next_to_finish()
#cam.start_playing()
