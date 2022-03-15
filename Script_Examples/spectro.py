from nion.swift.model import HardwareSource
import numpy
import time
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API

spec = HardwareSource.HardwareSourceManager().get_instrument_by_id("optSpec_controller DEBUG")
cam_eels = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")

step = 10
start = 500
end = 600+step
acq_time = 2
for x in numpy.arange(start, end, step):
    spec.wav_f = x
    time.sleep(2)
    cam_eels.start_playing()
    time.sleep(acq_time)
    cam_eels.stop_playing()
    print(spec.wav_f)
