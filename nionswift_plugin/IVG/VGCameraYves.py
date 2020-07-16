# standard libraries
import copy
import ctypes
import gettext
import numpy
import threading
import typing
import time
import json
import traceback
import os
from enum import Enum

# local libraries

from nion.swift.model import PlugInManager
from nion.swift.model import HardwareSource
from nion.utils import Registry

from nion.instrumentation import camera_base

from . import orsaycamera

from . import ivg_inst

_ = gettext.gettext

# STEM_CONTROLLER_ID = "autostem_controller"

class Orsay_Data(Enum):
    s16 = 2
    s32 = 3
    uns16 = 6
    uns32 = 7
    float = 11
    real = 12

class CameraDevice(camera_base.CameraDevice):

    def __init__(self, manufacturer, model, sn, simul, instrument: ivg_inst.ivgInstrument, id, name):
        self.camera_id=id
        self.camera_type="eels"
        self.camera_name=name
        self.instrument=instrument
        self.camera = orsaycamera.orsayCamera(manufacturer, model, sn, simul)
        self.__config_dialog_handler = None
        self.__sensor_dimensions = self.camera.getCCDSize()
        self.__readout_area = 0, 0, *self.__sensor_dimensions
        self.__orsay_binning = self.camera.getBinning()
        self.__exposure_time = 0
        self.__is_vg = True
        self.sizex, self.sizey = self.camera.getImageSize()
        self.sizez = 1
        self._last_time = time.time()
        self.frame_parameter_changed_event = Event.Event()

        # register data locker for focus acquisition
        self.fnlock = orsaycamera.DATALOCKFUNC(self.__data_locker)
        self.camera.registerDataLocker(self.fnlock)
        self.fnunlock = orsaycamera.DATAUNLOCKFUNC(self.__data_unlocker)
        self.camera.registerDataUnlocker(self.fnunlock)
        self.imagedata = None
        self.imagedata_ptr = None
        self.acquire_data = None
        self.has_data_event = threading.Event()

        #makes sure there is a calibration that does not depends on calibration_controls if we are not using a stem_controller, for example if we are not working with AS2
        #swift checks first for a propertie called calibration in the data item; if none, it checks for a calibration method for the camera, if none it checks for calibration_controls
        #if self.__is_vg:
        #    self.calibration= [Calibration.Calibration().rpc_dict,Calibration.Calibration(offset=100, scale=100, units="eV").rpc_dict]
        bx, by = self.camera.getBinning()
        port = self.camera.getCurrentPort()

        d = {
            "exposure_ms": 10,
            "h_binning": bx,
            "v_binning": by,
            "soft_binning": False,
            "acquisition_mode": "Focus",
            "spectra_count": 10,
            "multiplication": self.camera.getMultiplication()[0],
            "area": self.camera.getArea(),
            "port": port,
            "speed": self.camera.getCurrentSpeed(port),
            "gain": self.camera.getGain(port),
            "turbo_mode_enabled": self.camera.getTurboMode()[0],
            "video_threshold": self.camera.getVideoThreshold(),
            "fan_enabled": self.camera.getFan(),
            "processing": None
        }


        self.current_camera_settings = CameraFrameParameters(d)
        self.__hardware_settings = self.current_camera_settings

        self.camera.setAccumulationNumber(self.current_camera_settings.spectra_count)
        self.frame_number = 0

        self.__processing = None

        self.__acqon = False
        self.__acqspimon = False

        self.__calibration_controls = {}

        if manufacturer == 2:
            self.camera.setCCDOverscan(128,0)

    @property
    def binning_values(self) -> typing.List[int]:
        return [1, 2, 5, 10, 20, 50, 200]

    def close(self):
        self.camera.stopSpim(True)
        #self.camera.close()

    def create_frame_parameters(self, d: dict) -> dict:
        return self.current_camera_settings

    def set_frame_parameters(self, frame_parameters : dict) -> None:
        if self.__acqon: self.stop_live()
            
        if self.__hardware_settings.exposure_ms != frame_parameters.exposure_ms:
            self.__hardware_settings.exposure_ms = frame_parameters.exposure_ms
            self.camera.setExposureTime(frame_parameters.exposure_ms/1000.)
            if self.frame_parameter_changed_event is not None:
                self.frame_parameter_changed_event.fire("exposure_ms")

        if "acquisition_mode" in frame_parameters:
            if self.frame_parameter_changed_event is not None:
                self.frame_parameter_changed_event.fire("acquisition_mode")

        if "soft_binning" in frame_parameters:
            self.__hardware_settings.soft_binning = frame_parameters.soft_binning
            if self.__hardware_settings.acquisition_mode != frame_parameters.acquisition_mode:
                self.__hardware_settings.acquisition_mode = frame_parameters.acquisition_mode
            print(f"acquisition mode[camera]: {self.__hardware_settings.acquisition_mode}")
            self.__hardware_settings.spectra_count = frame_parameters.spectra_count

        if "port" in frame_parameters:
            if self.__hardware_settings.port != frame_parameters.port:
                self.__hardware_settings.port = frame_parameters.port
                self.camera.setCurrentPort(frame_parameters.port)

        if "speed" in frame_parameters:
            if self.__hardware_settings.speed != frame_parameters.speed:
                self.__hardware_settings.speed = frame_parameters.speed
                self.camera.setSpeed(self.__hardware_settings.port, frame_parameters.speed)

        if "area" in frame_parameters:
            if any(i != j for i,j in zip(self.__hardware_settings.area, frame_parameters.area)):
                # if change area, put back binning to 1,1 temporarily in order to avoid conflicts, binnig will then be setup later
                self.__hardware_settings.h_binning = 1
                self.__hardware_settings.v_binning = 1
                self.camera.setBinning(self.__hardware_settings.h_binning, self.__hardware_settings.v_binning)
                self.__hardware_settings.area = frame_parameters.area
                self.camera.setArea(self.__hardware_settings.area)

        if ("h_binning" in frame_parameters) and ("v_binning" in frame_parameters):
            if (self.__hardware_settings.h_binning != frame_parameters.h_binning) \
                    or (self.__hardware_settings.v_binning != frame_parameters.v_binning):
                self.camera.setBinning(frame_parameters.h_binning, frame_parameters.v_binning)
                self.__hardware_settings.h_binning, self.__hardware_settings.v_binning = self.camera.getBinning()

        if "gain" in frame_parameters:
            if self.__hardware_settings.gain != frame_parameters.gain:
                self.__hardware_settings.gain = frame_parameters.gain
                self.camera.setGain(self.__hardware_settings.gain)
        if "spectra_count" in frame_parameters:
            self.__hardware_settings.spectra_count = frame_parameters.spectra_count
            self.camera.setAccumulationNumber(self.__hardware_settings.spectra_count)
        if "video_threshold" in frame_parameters:
            self.__hardware_settings.video_threshold = frame_parameters.video_threshold
            self.camera.setVideoThreshold(self.__hardware_settings.video_threshold)
        if "fan_enabled" in frame_parameters:
            self.__hardware_settings.fan_enabled = frame_parameters.fan_enabled
            self.camera.setFan(self.__hardware_settings.fan_enabled)

        if "processing" in frame_parameters:
            self.__hardware_settings.processing = frame_parameters.processing

        if self.__acqon: self.start_live()

    def __numpy_to_orsay_type(self, array: numpy.array):
        orsay_type = Orsay_Data.float
        if array.dtype == numpy.double:
            orsay_type = Orsay_Data.real
        if array.dtype == numpy.int16:
            orsay_type = Orsay_Data.s16
        if array.dtype == numpy.int32:
            orsay_type = Orsay_Data.s32
        if array.dtype == numpy.uint16:
            orsay_type = Orsay_Data.uns16
        if array.dtype == numpy.uint32:
            orsay_type = Orsay_Data.uns32
        return orsay_type.value

    def __connection_listener(self, changed: bool, message: bool):
        if message:
            print("Message connection changed: " + changed)
        else:
            print("Data connection changed: " + changed)

    def __data_locker(self, gene, data_type, sx, sy, sz):
        sx[0] = self.sizex
        sy[0] = self.sizey
        sz[0] = 1
        data_type[0] = self.__numpy_to_orsay_type(self.imagedata)
        return self.imagedata_ptr.value

    def __data_unlocker(self, gene, new_data):
        self.frame_number += 1
        status = self.camera.getCCDStatus()
        if new_data:
            t = time.time()
            if t - self._last_time > 0.1:
                self.has_data_event.set()
                self._last_time = t
        if status["mode"] == "Cumul":
            self.frame_number = status["accumulation_count"]
        if status["mode"] == "idle":
            hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                self.camera_id)
            hardware_source.stop_playing()



    def __spectrum_data_locker(self, gene, data_type, sx) -> None:
        if self.__acqon and self.__acqspimon and (self.current_camera_settings.exposure_ms >= 10):
            sx[0] = self.sizex
            data_type[0] = self.__numpy_to_orsay_type(self.imagedata)
            return self.imagedata_ptr.value
        else:
            return None

    @property
    def sensor_dimensions(self) -> (int, int):
        return self.__sensor_dimensions

    @property
    def readout_area(self) -> (int, int, int, int):
        return self.__readout_area

    @readout_area.setter
    def readout_area(self, readout_area_TLBR: (int, int, int, int)) -> None:
        self.__readout_area = readout_area_TLBR

    @property
    def flip(self):
        return False

    @flip.setter
    def flip(self, do_flip):
        pass

    def start_live(self) -> None:
        api_broker = PlugInManager.APIBroker()
        api = api_broker.get_api(version='~1.0', ui_version='~1.0')
        self.__data_item_display = api.library.get_data_item_for_reference_key(self.camera_id)

        self.frame_number = 0
        self.sizex, self.sizey = self.camera.getImageSize()
        if self.current_camera_settings.soft_binning:
            self.sizey = 1
        print(f"Start live, Image size: {self.sizex} x {self.sizey}"
              f"  soft_binning: {self.current_camera_settings.soft_binning}"
              f"    mode: {self.current_camera_settings.acquisition_mode}"
              f"    nb spectra {self.current_camera_settings.spectra_count}")
        self.camera.setAccumulationNumber(self.current_camera_settings.spectra_count)

        self.sizez = 1
        acqmode = 0
        sb = "1d" if self.current_camera_settings.soft_binning else "2d"
        if self.current_camera_settings.acquisition_mode == "Cumul":
            acqmode = 1

        self.imagedata = numpy.zeros((self.sizey, self.sizex), dtype=numpy.float32)
        self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
        self.__acqon = self.camera.startFocus(self.current_camera_settings.exposure_ms / 1000, sb, acqmode)

        self._last_time = time.time()

    def stop_live(self) -> None:
        self.__acqon = self.camera.stopFocus()

    def acquire_image(self) -> dict:
        gotit = self.has_data_event.wait(1)
        self.has_data_event.clear()
        acquisition_mode = self.current_camera_settings.acquisition_mode
        self.acquire_data = self.imagedata
        if self.acquire_data.shape[0] == 1:
            datum_dimensions = 1
            collection_dimensions = 1
        else:
            datum_dimensions = 2
            collection_dimensions = 0
        properties = dict()
        properties["frame_number"] = self.frame_number
        properties["acquisition_mode"] = acquisition_mode
        calibration_controls = copy.deepcopy(self.calibration_controls)

        return {"data": self.acquire_data, "collection_dimension_count": collection_dimensions,
                "datum_dimension_count": datum_dimensions, "calibration_controls": calibration_controls,
                "properties": properties}

    @property
    def calibration_controls(self) -> dict:
        """Define the AS2 calibration controls for this camera.

        The controls should be unique for each camera if there are more than one.
        """
        return {
            "x_scale_control": self.camera_type + "_x_scale",
            "x_offset_control": self.camera_type + "_x_offset",
            "x_units_value": "eV",
            "y_scale_control": self.camera_type + "_y_scale",
            "y_offset_control": self.camera_type + "_y_offset",
            "y_units_value": "",
            "intensity_units_value": "counts",
            "counts_per_electron_value": 1
        }
        #return self.__calibration_controls


    #@calibration_controls.setter
    #def calibrations_controls(self, value: dict):
    #    """ Instrument owner will give controls names, override default camera eels calibration"""
    #    self.__calibration_controls = value

    @property
    def processing(self) -> typing.Optional[str]:
        return self.__processing

    @processing.setter
    def processing(self, value: str) -> None:
        self.__processing = value

    def get_expected_dimensions(self, binning: int) -> (int, int):
        return self.__sensor_dimensions

    def start_monitor(self) -> None:
        pass

    # custom methods (not part of the camera_base.Camera)

    @property
    def fan_enabled(self) -> bool:
        return self.camera.getFan()

    @fan_enabled.setter
    def fan_enabled(self, value: bool) -> None:
        self.camera.setFan(bool(value))

    def isCameraAcquiring(self):
        # acqon = self.camera.getCCDStatus()[0] != "idle"
        return self.__acqon

    def __getTurboMode(self):
        value, hs, vs = self.camera.getTurboMode()
        print(f"turbo mode : {value}")
        return value

    @property
    def readoutTime(self) -> float:
        return self.camera.getReadoutTime()

    def get_acquire_sequence_metrics(self, camera_frame_parameters: typing.Dict) -> typing.Dict:
        acquisition_frame_count = camera_frame_parameters.get("acquisition_frame_count")
        storage_frame_count = camera_frame_parameters.get("storage_frame_count")
        frame_time = self.current_camera_settings.exposure_ms / 1000 + self.camera.getReadoutTime()
        acquisition_time = frame_time * acquisition_frame_count
        if camera_frame_parameters.get("processing") == "sum_project":
            acquisition_memory = self.camera.getImageSize()[0] * 4 * acquisition_frame_count
            storage_memory = self.camera.getImageSize()[0] * 4 * storage_frame_count
        else:
            acquisition_memory = self.camera.getImageSize()[0] * self.camera.getImageSize()[1] * 4 * acquisition_frame_count
            storage_memory = self.camera.getImageSize()[0] * self.camera.getImageSize()[1] * 4 * storage_frame_count
        return { "acquisition_time": acquisition_time, "acquisition_memory": acquisition_memory, "storage_memory": storage_memory }


class CameraFrameParameters(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
        self.exposure_ms = self.get("exposure_ms", 125)  # milliseconds
        self.h_binning = self.get("h_binning", 1)
        self.v_binning = self.get("v_binning", 1)
        self.soft_binning = self.get("soft_binning", True)  # 1d, 2d
        self.acquisition_mode = self.get("acquisition_mode", "Focus")  # Focus, Cumul, 1D-Chrono, 1D-Chrono-Live, 2D-Chrono
        self.spectra_count = self.get("spectra_count", 1)
        self.speed = self.get("speed", 1)
        self.gain = self.get("gain", 0)
        self.multiplication = self.get("multiplication", 1)
        self.port = self.get("port", 0)
        self.area = self.get("area", (0, 0, 2048, 2048))  # a tuple: top, left, bottom, right
        self.turbo_mode_enabled = self.get("turbo_mode_enabled", False)
        self.video_threshold = self.get("video_threshold", 0)
        self.fan_enabled = self.get("fan_enabled", False)
        self.integration_count = 1  # required

    def __copy__(self):
        return self.__class__(copy.copy(dict(self)))

    def __deepcopy__(self, memo):
        deepcopy = self.__class__(copy.deepcopy(dict(self)))
        memo[id(self)] = deepcopy
        return deepcopy

    @property
    def binning(self):
        return self.h_binning

    @binning.setter
    def binning(self, value):
        self.h_binning = value

    def as_dict(self):
        return {
            "exposure_ms": self.exposure_ms,
            "h_binning": self.h_binning,
            "v_binning": self.v_binning,
            "soft_binning": self.soft_binning,
            "acquisition_mode": self.acquisition_mode,
            "spectra_count": self.spectra_count,
            "speed": self.speed,
            "gain": self.gain,
            "multiplication": self.multiplication,
            "port": self.port,
            "area": self.area,
            "turbo_mode_enabled": self.turbo_mode_enabled,
            "video_threshold": self.video_threshold,
            "fan_enabled": self.fan_enabled
        }


from nion.utils import Event

class CameraSettings:

    def __init__(self, camera_device: CameraDevice):
        # these events must be defined
        self.current_frame_parameters_changed_event = Event.Event()
        self.record_frame_parameters_changed_event = Event.Event()
        self.profile_changed_event = Event.Event()
        self.frame_parameters_changed_event = Event.Event()
        self.settings_changed_event = Event.Event()
        # the list of possible modes should be defined here
        self.modes = ["Focus", "Cumul"]

        self.__camera_device = camera_device
        self.settings_id = camera_device.camera_id

    def close(self):
        pass

    def initialize(self, **kwargs):
        pass

    def apply_settings(self, settings_dict: typing.Dict) -> None:
        """Initialize the settings with the settings_dict."""
        if isinstance(settings_dict, dict):
            self.__frame_parameters = CameraFrameParameters(settings_dict)
            self.__record_parameters = copy.deepcopy(settings_dict)
            self.__camera_device.current_camera_settings = self.__frame_parameters
            self.settings_changed_event.fire(self.__frame_parameters)

    def __save_settings(self) -> typing.Dict:
        return self.__frame_parameters.as_dict()

    def get_frame_parameters_from_dict(self, d):
        return CameraFrameParameters(d)

    def set_current_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        self.__camera_device.current_camera_settings = frame_parameters
        self.settings_changed_event.fire(frame_parameters)
        self.current_frame_parameters_changed_event.fire(frame_parameters)
        self.record_frame_parameters_changed_event.fire(frame_parameters)

    def get_current_frame_parameters(self) -> CameraFrameParameters:
        return self.__camera_device.current_camera_settings

    def set_record_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        self.set_current_frame_parameters(frame_parameters)

    def get_record_frame_parameters(self) -> CameraFrameParameters:
        return self.get_current_frame_parameters()

    def set_frame_parameters(self, profile_index: int, frame_parameters) -> None:
        self.set_current_frame_parameters(frame_parameters)

    def get_frame_parameters(self, profile_index: int):
        return self.get_current_frame_parameters()

    def set_selected_profile_index(self, profile_index: int) -> None:
        pass

    @property
    def selected_profile_index(self) -> int:
        return 0

    def get_mode(self) -> str:
        return str()

    def set_mode(self, mode: str) -> None:
        pass

    def open_configuration_interface(self, api_broker) -> None:
        pass

    def open_monitor(self) -> None:
        pass


class CameraModule:

    def __init__(self, stem_controller_id: str, camera_device: CameraDevice, camera_settings: CameraSettings):
        self.stem_controller_id = stem_controller_id
        self.camera_device = camera_device
        self.camera_settings = camera_settings
        self.camera_panel_type = "orsay_camera_panel"


def periodic_logger():
    messages = list()
    data_elements = list()
    return messages, data_elements


def run(instrument: ivg_inst.ivgInstrument):
    cameras = list()
    try:
        config_file = os.environ['ALLUSERSPROFILE'] + "\\Nion\\Nion Swift\\Orsay_cameras_list.json"
        with open(config_file) as f:
            cameras = json.load(f)
    except Exception as e:
        cameras.append({"manufacturer": 1, "model": "KURO: 2048B", "type": "eels", "id": "orsay_camera_kuro", "name": "EELS", "simulation": True})
        cameras.append({"manufacturer": 1, "model": "ProEM+: 1600xx(2)B eXcelon", "type":"eire", "id":"orsay_camera_eire", "name": "EIRE", "simulation":True})

    for camera in cameras:
        print(camera["manufacturer"])
        sn=""
        camera_device = CameraDevice(camera["manufacturer"], camera["model"], sn, camera["simulation"], instrument, camera["id"], camera["name"])

        camera_settings = CameraSettings(camera_device)

        Registry.register_component(CameraModule("VG_Lum_controller", camera_device, camera_settings),
                                        {"camera_module"})
