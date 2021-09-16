from nion.swift.model import HardwareSource
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API
scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

scanInstrument.scan_device.orsayscan.SetTdcLine(1, 2, 7)  # Copy Line Start
#scanInstrument.scan_device.orsayscan.SetTdcLine(0, 2, 13)  # Copy line 05

scanInstrument.scan_device.orsayscan.SetFlybackTime(1.0e-6)