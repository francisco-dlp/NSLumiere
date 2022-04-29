import time
from nion.swift.model import HardwareSource
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API

cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

scan.scan_device.orsayscan.SetBottomBlanking(0, 14, beamontime=1e-6, delay=500e-9)
scan.scan_device.orsayscan.SetBottomBlanking(3, 14, risingedge=True, beamontime=10e-6, delay=500e-9)

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
