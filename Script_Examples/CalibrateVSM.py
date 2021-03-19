from nion.swift.model import HardwareSource

scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

drift_tube = {"offset": 0.005, "gain": 1.0/5.005}
scan.scan_device.orsayscan.drift_tube_calibration = drift_tube
scan.scan_device.orsayscan.drift_tube = 2.557

print('Current Settings')
print(scan.scan_device.orsayscan.drift_tube)
print(scan.scan_device.orsayscan.drift_tube_calibration)