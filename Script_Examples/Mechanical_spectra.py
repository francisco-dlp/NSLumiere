from nion.utils import Registry
from nion.swift.model import HardwareSource
import numpy
import time

cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eels")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
stage = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
my_inst = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")

pts = 16

xarray = numpy.linspace(-0.5, 0.5, pts)
yarray = numpy.linspace(-0.5, 0.5, pts)

fov = scan.scan_device.field_of_view
ia = scan.scan_device.Image_area

x_samp = (fov*1e9)/(ia[3]-ia[2])
y_samp = (fov*1e9)/(ia[5]-ia[4])

initial_stage_x = stage.x_pos_f
initial_stage_y = stage.y_pos_f

initial_probe_x = scan.scan_device.probe_pos[0]
initial_probe_y = scan.scan_device.probe_pos[1]

initial_probe_pixel = scan.scan_device._Device__probe_position_pixels

print(f'Probe Sampling Precision (nm): {x_samp} nm and {y_samp} nm.')
print(f'Mechanical step is (nm): {(fov*1e9)/pts} and {(fov*1e9)/pts}')
print(f'Image area (pixels): {(ia[3]-ia[2])} and {(ia[5]-ia[4])}')
print(f'Pixels per step: {(ia[3]-ia[2])/pts} and {(ia[5]-ia[4])/pts}')
print(f'initial probe position is {initial_probe_x} and {initial_probe_y}')
print(f'initial probe position (in pixels) is {initial_probe_pixel}')

sen = 1
for x in xarray:
    stage.x_pos_f = initial_stage_x + x*fov*1e8 #You put 400 to have 4 microns in this property here
    print(scan.scan_device.probe_pos)
    sen = sen * -1
    for y in yarray:
        if not my_inst._ivgInstrument__stage_moving or True:
            stage.y_pos_f = initial_stage_y + y*fov*1e8
            scan.scan_device.probe_pos = ((x+1.0)*0.5, (y+1.0)*0.5)
        time.sleep(0.01)

stage.x_pos_f = initial_stage_x
stage.y_pos_f = initial_stage_y
scan.scan_device.probe_pos = (initial_probe_x, initial_probe_y)

