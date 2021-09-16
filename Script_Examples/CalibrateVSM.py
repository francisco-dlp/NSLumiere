from nion.swift.model import HardwareSource
import time

scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")




#print(dir(scan.scan_device.orsayscan))

drift_tube = {"offset": 0.002, "gain": 1.0/5.005}
scan.scan_device.orsayscan.drift_tube_calibration = drift_tube
scan.scan_device.orsayscan.drift_tube = 0.5

#print('Current Settings')
#print(scan.scan_device.orsayscan.drift_tube)
#print(scan.scan_device.orsayscan.drift_tube_calibration)



print(scan.scan_device.orsayscan.drift_tube)
print(scan.scan_device.orsayscan.drift_tube_calibration)
print(scan.scan_device.orsayscan.GetVSM())