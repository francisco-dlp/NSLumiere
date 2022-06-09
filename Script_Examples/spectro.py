from nion.swift.model import HardwareSource
import numpy
import time
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API

spec = HardwareSource.HardwareSourceManager().get_instrument_by_id("optSpec_controller PRINCETON")
cam_eels = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_timepix3")
cam_eire = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_eire")

step = 10
start = 500
end = 700 + step
acq_time = 3


def set_wav(spec, wl, step):
    spec.wav_f = wl
    time.sleep(step * 1 / 10)
    print('Current wav: ' + spec.wav_f)


def set_slit(spec, exiS, entS):
    spec.entrance_slit_f = entS
    spec.exit_slit_f = exiS
    spec.which_slit_f = 1


def acquire_and_stop(cam_eels, acq_time):
    cam_eels.start_playing()
    time.sleep(acq_time + 1)
    cam_eels.stop_playing()


# Setting up
cam_eels._CameraHardwareSource2__camera.camera.setCurrentPort(1)
#set_slit(spec, exiS, entS)
set_wav(spec, start, step)

# main loop
for x in numpy.arange(start, end, step):
    set_wav(spec, x, step)
    acquire_and_stop(cam_eels, acq_time)

# Finishing acquisition
cam_eels._CameraHardwareSource2__camera.camera.setCurrentPort(0)


"""
for x in numpy.arange(start, end, step):
    spec.wav_f = x
    time.sleep(2)
    class TimePix3():

        self.__port = 1
    cam_eels.start_playing()
    time.sleep(acq_time)
    cam_eels.stop_playing()
    print(spec.wav_f)
"""
