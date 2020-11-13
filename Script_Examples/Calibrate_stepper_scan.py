from nion.swift.model import HardwareSource
import numpy
import time
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.utils import Geometry
from nion.swift.model import Graphics

api = api_broker.get_api(API.version, UI.version)

scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
stage = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
my_inst = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")


'''
xdata = numpy.random.randn(10, 10, 1024)
intensity_calibration = api.create_calibration(offset=0.0, scale=4.0, units='counts')
dimensional_calibration_0 = api.create_calibration(0.0, 10, '0U')
dimensional_calibration_1 = api.create_calibration(0.0, 20, '1U')
dimensional_calibration_2 = api.create_calibration(0.0, 30, '2U')
dimensional_calibrations = [dimensional_calibration_0, dimensional_calibration_1, dimensional_calibration_2]
si_data_descriptor = api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=1)
si_xdata = api.create_data_and_metadata(xdata, data_descriptor=si_data_descriptor,
                                        intensity_calibration=intensity_calibration,
                                        dimensional_calibrations=dimensional_calibrations)
data_item = api.library.create_data_item_from_data_and_metadata(si_xdata)
'''

pts = 4
sub_region = 0.4

xarray = numpy.linspace(-sub_region, sub_region, pts+1)
yarray = numpy.linspace(-sub_region, sub_region, pts+1)

fov = scan.scan_device.field_of_view
ia = scan.scan_device.Image_area

x_samp = (fov)/(ia[0])
y_samp = (fov)/(ia[1])

initial_stage_x = stage.x_pos_f
initial_stage_y = stage.y_pos_f

if scan.probe_position is None:
    raise Exception("***MECHANICAL SPECTRA***: Probe position not assigned. Position the probe using Scan Control.")

initial_probe_x, initial_probe_y = scan.probe_position


if abs(initial_probe_x-0.5)>0.01 or abs(initial_probe_y-0.5)>0.01:
    raise Exception("***MECHANICAL SPECTRA***: Put probe close to (0.5, 0.5). 1% tolerance allowed. ")

if not (ia[0]/pts).is_integer() or not (ia[1]/pts).is_integer():
    raise Exception("***MECHANICAL SPECTRA***: Number of points (pts) is not a divisor of image area (in pixels)")

print(f'Probe Sampling Precision (nm): {x_samp} nm and {y_samp} nm.')
print(f'Mechanical step is (nm): {(fov*1e9)/pts} and {(fov*1e9)/pts}')
print(f'Image area (pixels): {(ia[0])} and {(ia[1])}')
print(f'Pixels per step: {(ia[0])/pts} and {(ia[1])/pts}')
print(f'initial probe position is {initial_probe_x} and {initial_probe_y}')

xdata = numpy.zeros((pts+1, pts+1, ia[0], ia[1]))

def highlight_data(data, index, shape, w, value, sen):
    x, y = index
    cx = (x)*shape[0]
    cy = (y)*shape[1] if sen==1 else shape[1] - (y)*shape[1]
    data[int(cy-w):int(cy+w), int(cx-w):int(cx+w)] = value

def calib(x, y):
    xc = (ia[0]/2 + 389.125*x - 45.75*y)/ia[0]
    yc = (ia[1]/2 + 94.875*x + 380.375*y)/ia[1]
    return (xc, yc)

sen = 1
stage.x_pos_f = initial_stage_x + sub_region*fov*1e8
stage.y_pos_f = initial_stage_y - sub_region*fov*1e8*sen
time.sleep(1.0)

for xi, x in enumerate(xarray):
    sen = sen * 1
    stage.x_pos_f = initial_stage_x - x*fov*1e8
    for yi, y in enumerate(yarray):
        for val in my_inst._ivgInstrument__stage_moving:
            if val:
                raise Exception("***MECHANICAL SPECTRA***: Motor move during a new command.")
        stage.y_pos_f = initial_stage_y + y*fov*1e8*sen
        time.sleep(1.0) if yi==0 else time.sleep(0.5)
        im = scan.grab_next_to_start()
        highlight_data(im[0].data, calib(x, y), (ia[0], ia[1]), 1, 2, sen)
        if sen==1:
            xdata[xi, yi] = im[0].data
        else:
            xdata[xi, pts-1-yi] = im[0].data


si_data_descriptor = api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=2)
si_xdata = api.create_data_and_metadata(xdata, data_descriptor=si_data_descriptor)
data_item = api.library.create_data_item_from_data_and_metadata(si_xdata)

stage.x_pos_f = initial_stage_x
stage.y_pos_f = initial_stage_y

