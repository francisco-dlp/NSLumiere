from nion.utils import Registry
from nion.swift.model import HardwareSource
import numpy
import time

cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eels")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
stage = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
my_inst = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")

pts = 16

xarray = numpy.linspace(0, 1, pts)
yarray = numpy.linspace(0, 1, pts)

fov = scan.scan_device.field_of_view
ia = scan.scan_device.Image_area

x_samp = (fov*1e9)/ia[0]
y_samp = (fov*1e9)/ia[1]

initial_x = stage.x_pos_f
initial_y = stage.y_pos_f

print(x_samp)
print(stage.x_pos_f/100)
print(stage.y_pos_f/100)
sen = 1
for x in yarray:

    stage.x_pos_f+=x_samp/10 * (ia[3]-ia[2])/pts
    sen = sen * -1
    for y in xarray:
        stage.y_pos_f+=y_samp/10 * sen * (ia[5]-ia[4])/pts
        time.sleep(0.05)
        #scan.scan_device.probe_pos = (x, y)

print(stage.x_pos_f/100)
print(stage.y_pos_f/100)

stage.x_pos_f = initial_x
stage.y_pos_f = initial_y