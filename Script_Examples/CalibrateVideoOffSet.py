from nion.swift.model import HardwareSource

scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

#scan.scan_device.orsayscan.setVideoOffset(1, 0.0)
print(scan.scan_device.orsayscan.getVideoOffset(0))