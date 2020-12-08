from nion.swift.model import HardwareSource
import numpy
import time
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API

cam_eels = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eels")
cam_eire = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")
scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
stage = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
my_inst = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")

pts = 32
sub_region = 0.45

i_obj = my_inst._ivgInstrument__obj_cur

xarray = numpy.linspace(-sub_region, sub_region, pts+1)
yarray = numpy.linspace(-sub_region, sub_region, pts+1)

fov = scan.scan_device.field_of_view
time_us = scan.scan_device.current_frame_parameters['pixel_time_us']
ia = scan.scan_device.Image_area
texp = cam_eire.get_current_frame_parameters()['exposure_ms']/1000.
tstepper = 0.20*(32/pts)*(fov/6.4e-5)

x_samp = (fov*1e9)/(ia[3]-ia[2])
y_samp = (fov*1e9)/(ia[5]-ia[4])

initial_stage_x = stage.x_pos_f
initial_stage_y = stage.y_pos_f

initial_probe_x = scan.scan_device.probe_pos[0]
initial_probe_y = scan.scan_device.probe_pos[1]

initial_probe_pixel = scan.scan_device._Device__probe_position_pixels

IMAGING = False

#if texp<tstepper:
#    raise Exception("***MECHANICAL SPECTRA***: Camera exposition is smaller than the stepper sleep. You might lose exposition time for no reason.")

if ia!=[1024, 1024, 0, 1024, 0, 1024]:
    raise Exception("***MECHANICAL SPECTRA***: Put scan with 1024x1024 pixels.")

if abs(initial_probe_x-0.5)>0.01 or abs(initial_probe_y-0.5)>0.01:
    raise Exception("***MECHANICAL SPECTRA***: Put probe close to (0.5, 0.5). 1% tolerance allowed.")

print(((ia[3]-ia[2])/pts).is_integer())

if not ((ia[3]-ia[2])/pts).is_integer() or not ((ia[5]-ia[4])/pts).is_integer():
    raise Exception("***MECHANICAL SPECTRA***: Number of points (pts) is not a divisor of image area (in pixels)")

print(f'Probe Sampling Precision (nm): {x_samp} nm and {y_samp} nm.')
print(f'Mechanical step is (nm): {(fov*1e9)/(pts+1)} and {(fov*1e9)/(pts+1)}')
print(f'Image area (pixels): {(ia[3]-ia[2])} and {(ia[5]-ia[4])}')
print(f'Pixels per step: {(ia[3]-ia[2])/pts} and {(ia[5]-ia[4])/pts}')
print(f'initial probe position is {initial_probe_x} and {initial_probe_y}')
print(f'initial probe position (in pixels) is {initial_probe_pixel}')
print('Approximate measurement time is '+format((pts*2.0/60. + 1/60.*pts**2*max(texp, tstepper)), '.1f')+' min.')

def highlight_data(data, index, shape, w, value, sen):
    x, y = index
    cx = (x)*shape[0]
    cy = (y)*shape[1] if sen==1 else shape[1] - (y)*shape[1]
    data[int(cy-w):int(cy+w), int(cx-w):int(cx+w)] = value

def calib_and_invert(x, y):
    xc = (0.4800625 + 0.79845486*x - 0.08020833*y)
    yc = (0.45892969 + 0.17607639*x + 0.73942708*y)
    return (yc, xc)

def calib(x, y):
    xc = (0.4800625 + 0.79845486*x - 0.08020833*y)
    yc = (0.45892969 + 0.17607639*x + 0.73942708*y)
    return (xc, yc)

def moving():
    for val in my_inst._ivgInstrument__stage_moving:
        if val:
            return True
    return False

stage.x_pos_f = initial_stage_x + sub_region*fov*1e8
stage.y_pos_f = initial_stage_y - sub_region*fov*1e8

cam_eire.start_playing()
scan.stop_playing()
xdata = numpy.zeros((pts+1, pts+1, 1600))
xdata02 = numpy.zeros((pts+1, pts+1, ia[0], ia[1]))
time.sleep(2.0)

## Setting our first Data_Item
data = cam_eire.grab_next_to_finish()
si_data_descriptor = api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=1)
dimensional_calibration_0 = api.create_calibration(-(sub_region*fov*1e9), (2*sub_region*fov*1e9)/(pts+1), 'nm') #x
dimensional_calibration_1 = api.create_calibration(-(sub_region*fov*1e9), (2*sub_region*fov*1e9)/(pts+1), 'nm') #y
dimensional_calibration_2 = data[0].get_dimensional_calibration(1) #from camera
dimensional_calibrations =  [dimensional_calibration_0, dimensional_calibration_1, dimensional_calibration_2]
si_xdata = api.create_data_and_metadata(xdata, data_descriptor=si_data_descriptor,
                                        dimensional_calibrations=dimensional_calibrations)
data_item = api.library.create_data_item_from_data_and_metadata(si_xdata)
data_item.title = 'Mech_Spec_'+format(2*sub_region*(fov*1e9)/(pts+1), '.2f')+' nm_'+ \
                  str(cam_eire.get_current_frame_parameters()['exposure_ms'])+' ms_' + \
                  str(scan.scan_device.Image_area) + 'IA_' + str(i_obj) + 'Obj. Amps'


sen = 1
for xi, x in enumerate(xarray):
    print('Percentage dones is: ' + format((100*xi/len(xarray)), '.2f') + ' %')
    stage.x_pos_f = initial_stage_x - x*fov*1e8 #You put 400 to have 4 microns in this property here
    sen = sen * 1
    for yi, y in enumerate(yarray):
        if moving(): print(f"***MECHANICAL SPECTRA***: Motor move during a new command at point {(xi, yi)}")
        stage.y_pos_f = initial_stage_y + y*fov*1e8*sen
        time.sleep(1.0) if yi==0 else time.sleep(0.1)

        while moving():
            #print('***MECHANICAL SPECTRA***: Still moving. Will set probe afterwards')
            time.sleep(0.1)

        scan.scan_device.probe_pos = (calib_and_invert(x, y))

        data = cam_eire.grab_next_to_start()
        data_item.data[yi, xi] = data[0].data

        if IMAGING:
            scan.start_playing()
            time.sleep((time_us/1000000)*ia[0]*ia[1]*2.0)
            im = scan.grab_next_to_start()
            scan.stop_playing()
            highlight_data(im[0].data, calib(x, y), (ia[0], ia[1]), 3, 2, sen)
            xdata02[xi, yi] = im[0].data
            while scan.is_playing:
                #print('***MECHANICAL SPECTRA***: Still scanning')
                time.sleep(0.1)

if IMAGING:
    ## Setting our second Data_Item. I put it at end because you can kind of check it real time anyways
    si_data02_descriptor = api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=2)
    si_xdata02 = api.create_data_and_metadata(xdata02, data_descriptor=si_data02_descriptor)
    data_item02 = api.library.create_data_item_from_data_and_metadata(si_xdata02)
    data_item02.title = 'Points_Mech_Spec_'+format(2*sub_region*(fov*1e9)/(pts+1), '.2f')+' nm_'+ \
                        str(cam_eire.get_current_frame_parameters()['exposure_ms'])+' ms_' + \
                        str(scan.scan_device.Image_area) + 'IA_' + str(i_obj) + 'Obj. Amps'

stage.x_pos_f = initial_stage_x
stage.y_pos_f = initial_stage_y
scan.scan_device.probe_pos = (initial_probe_x, initial_probe_y)
scan.start_playing()

