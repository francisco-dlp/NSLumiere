from nion.swift.model import HardwareSource
import numpy
import time

cam_eels = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eels")
cam_eire = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
stage = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
my_inst = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")

pts = 4
sub_region = 0.25

xarray = numpy.linspace(-sub_region, sub_region, pts)
yarray = numpy.linspace(-sub_region, sub_region, pts)

fov = scan.scan_device.field_of_view
ia = scan.scan_device.Image_area

x_samp = (fov*1e9)/(ia[3]-ia[2])
y_samp = (fov*1e9)/(ia[5]-ia[4])

initial_stage_x = stage.x_pos_f
initial_stage_y = stage.y_pos_f

initial_probe_x = scan.scan_device.probe_pos[0]
initial_probe_y = scan.scan_device.probe_pos[1]

initial_probe_pixel = scan.scan_device._Device__probe_position_pixels

if abs(initial_probe_x-0.5)>0.01 or abs(initial_probe_y-0.5)>0.01:
    raise Exception("***MECHANICAL SPECTRA***: Put probe close to (0.5, 0.5). 1% tolerance allowed. ")

print(((ia[3]-ia[2])/pts).is_integer())

if not ((ia[3]-ia[2])/pts).is_integer() or not ((ia[5]-ia[4])/pts).is_integer():
    raise Exception("***MECHANICAL SPECTRA***: Number of points (pts) is not a divisor of image area (in pixels)")

print(f'Probe Sampling Precision (nm): {x_samp} nm and {y_samp} nm.')
print(f'Mechanical step is (nm): {(fov*1e9)/pts} and {(fov*1e9)/pts}')
print(f'Image area (pixels): {(ia[3]-ia[2])} and {(ia[5]-ia[4])}')
print(f'Pixels per step: {(ia[3]-ia[2])/pts} and {(ia[5]-ia[4])/pts}')
print(f'initial probe position is {initial_probe_x} and {initial_probe_y}')
print(f'initial probe position (in pixels) is {initial_probe_pixel}')

stage.x_pos_f = initial_stage_x - sub_region*fov*1e8 #You put 400 to have 4 microns in this property here
stage.y_pos_f = initial_stage_y - sub_region*fov*1e8
cam_eire.start_playing()
data = list()
time.sleep(0.25)

sen = -1
for xi, x in enumerate(xarray):
    stage.x_pos_f = initial_stage_x + x*fov*1e8 #You put 400 to have 4 microns in this property here
    sen = sen * -1
    for yi, y in enumerate(yarray):
        for val in my_inst._ivgInstrument__stage_moving:
            if val:
                raise Exception("***MECHANICAL SPECTRA***: Motor move during a new command.")
        stage.y_pos_f = initial_stage_y + y*fov*1e8*sen
        data = cam_eire.grab_next_to_finish()
        data.append([stage.x_pos_f, stage.y_pos_f, data[0]])
        #scan.scan_device.probe_pos = ((x+0.5), (y+0.5))

stage.x_pos_f = initial_stage_x
stage.y_pos_f = initial_stage_y
cam_eire.stop_playing()
#scan.scan_device.probe_pos = (initial_probe_x, initial_probe_y)

