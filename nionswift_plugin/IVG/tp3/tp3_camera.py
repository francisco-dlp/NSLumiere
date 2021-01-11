# standard libraries
import copy
import gettext
import typing
import logging
import threading

# local libraries
from nion.utils import Event
from nion.utils import Registry

from nionswift_plugin.IVG import ivg_inst
from . import tp3func

# other plug-ins
from nion.instrumentation import camera_base

_ = gettext.gettext

class Camera(camera_base.CameraDevice):
    """Implement a camera device."""

    def __init__(self, manufacturer, model, sn, simul, instrument: ivg_inst.ivgInstrument, id, name, type):
        self.camera_id = id
        self.camera_type = type
        self.camera_name = name

        self.__frame_number = 0
        self.__is_playing = False
        self.__readout_area = (0, 0, 256, 1024)

        self.__hasData = threading.Event()

        assert manufacturer=="4" #This tp3_camera is a demo for TimePix3. Manufacturer must be 4
        if manufacturer=='4':
            self.camera_callback = tp3func.SENDMYMESSAGEFUNC(self.sendMessageFactory())
            self.camera = tp3func.TimePix3(sn)
            self.tp3Listener = tp3func.ListenerTimePix3(self.camera_callback)

        self.frame_parameter_changed_event = Event.Event()
        self.stop_acquitisition_event = Event.Event()

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
            "processing": None,
            "flipped": False,
        }

        self.current_camera_settings = CameraFrameParameters(d)
        self.__hardware_settings = self.current_camera_settings

    def close(self):
        self.__is_playing = False

    @property
    def sensor_dimensions(self) -> (int, int):
        """Return the maximum sensor dimensions."""
        return (256, 1024)

    @property
    def readout_area(self) -> (int, int, int, int):
        """Return the readout area TLBR, returned in sensor coordinates (unbinned)."""
        return self.__readout_area

    @readout_area.setter
    def readout_area(self, readout_area_TLBR: (int, int, int, int)) -> None:
        """Set the readout area, specified in sensor coordinates (unbinned). Affects all modes."""
        self.__readout_area = readout_area_TLBR

    @property
    def flip(self):
        """Return whether data is flipped left-right (last dimension)."""
        return False

    @flip.setter
    def flip(self, do_flip):
        """Set whether data is flipped left-right (last dimension). Affects all modes."""
        pass

    @property
    def binning_values(self) -> typing.List[int]:
        """Return possible binning values."""
        return [1, 2, 4, 8]

    def get_expected_dimensions(self, binning: int) -> (int, int):
        readout_area = self.__readout_area
        return (readout_area[2] - readout_area[0]) // binning, (readout_area[3] - readout_area[1]) // binning

    def set_frame_parameters(self, frame_parameters) -> None:
        if self.__hardware_settings.exposure_ms != frame_parameters.exposure_ms:
            self.__hardware_settings.exposure_ms = frame_parameters.exposure_ms
            self.camera.setExposureTime(frame_parameters.exposure_ms / 1000.)

        if "soft_binning" in frame_parameters:
            self.__hardware_settings.soft_binning = frame_parameters.soft_binning
            if self.__hardware_settings.acquisition_mode != frame_parameters.acquisition_mode:
                self.__hardware_settings.acquisition_mode = frame_parameters.acquisition_mode
            print(f"***CAMERA***: acquisition mode[camera]: {self.__hardware_settings.acquisition_mode}")
            self.__hardware_settings.spectra_count = frame_parameters.spectra_count

        if "port" in frame_parameters:
            if self.__hardware_settings.port != frame_parameters.port:
                self.__hardware_settings.port = frame_parameters.port
                self.camera.setCurrentPort(frame_parameters.port)

    @property
    def calibration_controls(self) -> dict:
        """Define the STEM calibration controls for this camera.
        The controls should be unique for each camera if there are more than one.
        """
        return {
            "x_scale_control": self.camera_type + "_x_scale",
            "x_offset_control": self.camera_type + "_x_offset",
            "x_units_value": "eV" if self.camera_type == "eels" else "rad",
            "y_scale_control": self.camera_type + "_y_scale",
            "y_offset_control": self.camera_type + "_y_offset",
            "y_units_value": "" if self.camera_type == "eels" else "rad",
            "intensity_units_value": "counts",
            "counts_per_electron_value": 1
        }

    def start_live(self) -> None:
        """Start live acquisition. Required before using acquire_image."""
        if not self.__is_playing:
            self.__is_playing = True
            logging.info('***TP3***: Starting acquisition...')
            self.camera.finish_acq_simple()
            self.camera.start_acq_simple()
            self.tp3Listener.start_listening()
            #self.__clientThread = threading.Thread(target=self.acquire_single_frame, args=(8088,))
            #self.__clientThread.start()


    def stop_live(self) -> None:
        """Stop live acquisition."""
        self.__is_playing = False
        self.camera.finish_acq_simple()
        self.tp3Listener.finish_listening()
        #self.__clientThread.join()
        #self.__dataQueue = queue.LifoQueue()


    def acquire_image(self):
        """Acquire the most recent data."""

        self.__hasData.wait(2)
        self.__hasData.clear()
        #image_data = numpy.random.randn(256, 1024)
        self.acquire_data = self.imagedata

        datum_dimensions = 2
        collection_dimensions = 0

        properties = dict()
        properties["frame_number"] = self.__frame_number

        return {"data": self.acquire_data, "collection_dimension_count": collection_dimensions,
                "datum_dimension_count": datum_dimensions,
                "properties": properties}


    def sendMessageFactory(self):
        def sendMessage(message):
            if message:
                prop, last_bytes_data = self.tp3Listener.get_last_data()
                self.__frame_number = int(prop['frameNumber'])
                self.imagedata = self.tp3Listener.create_image_from_bytes(last_bytes_data)
                self.__hasData.set()
        return sendMessage

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
        self.flipped = self.get("flipped", False)
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
            "fan_enabled": self.fan_enabled,
            "flipped": self.flipped
        }


class CameraSettings:

    def __init__(self, camera_id: str):
        # these events must be defined
        self.current_frame_parameters_changed_event = Event.Event()
        self.record_frame_parameters_changed_event = Event.Event()
        self.profile_changed_event = Event.Event()
        self.frame_parameters_changed_event = Event.Event()

        # optional event and identifier for settings. defining settings_id signals that
        # the settings should be managed as a dict by the container of this class. the container
        # will call apply_settings to initialize settings and then expect settings_changed_event
        # to be fired when settings change.
        self.settings_changed_event = Event.Event()
        self.settings_id = camera_id

        self.__config_file = None

        self.__camera_id = camera_id

        # the list of possible modes should be defined here
        self.modes = ["Focus", "Cumul", "1D-Chrono", "1D-Chrono-Live"]

        # configure profiles
        self.__settings = [
            CameraFrameParameters({"exposure_ms": 100, "binning": 2}),
            CameraFrameParameters({"exposure_ms": 200, "binning": 2}),
            CameraFrameParameters({"exposure_ms": 500, "binning": 1}),
        ]

        self.__current_settings_index = 0

        self.__frame_parameters = copy.deepcopy(self.__settings[self.__current_settings_index])
        self.__record_parameters = copy.deepcopy(self.__settings[-1])

    def close(self):
        pass

    def initialize(self, **kwargs):
        pass

    def apply_settings(self, settings_dict: typing.Dict) -> None:
        """Initialize the settings with the settings_dict."""
        if isinstance(settings_dict, dict):
            settings_list = settings_dict.get("settings", list())
            if len(settings_list) == 3:
                self.__settings = [CameraFrameParameters(settings) for settings in settings_list]
            self.__current_settings_index = settings_dict.get("current_settings_index", 0)
            self.__frame_parameters = CameraFrameParameters(settings_dict.get("current_settings", self.__settings[0].as_dict()))
            self.__record_parameters = copy.deepcopy(self.__settings[-1])

    def __save_settings(self) -> typing.Dict:
        settings_dict = {
            "settings": [settings.as_dict() for settings in self.__settings],
            "current_settings_index": self.__current_settings_index,
            "current_settings": self.__frame_parameters.as_dict()
        }
        return settings_dict

    def get_frame_parameters_from_dict(self, d):
        return CameraFrameParameters(d)

    def set_current_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        """Set the current frame parameters.
        Fire the current frame parameters changed event and optionally the settings changed event.
        """
        self.__frame_parameters = copy.copy(frame_parameters)
        self.settings_changed_event.fire(self.__save_settings())
        self.current_frame_parameters_changed_event.fire(frame_parameters)

    def get_current_frame_parameters(self) -> CameraFrameParameters:
        """Get the current frame parameters."""
        return CameraFrameParameters(self.__frame_parameters)

    def set_record_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        """Set the record frame parameters.
        Fire the record frame parameters changed event and optionally the settings changed event.
        """
        self.__record_parameters = copy.copy(frame_parameters)
        self.record_frame_parameters_changed_event.fire(frame_parameters)

    def get_record_frame_parameters(self) -> CameraFrameParameters:
        """Get the record frame parameters."""
        return self.__record_parameters

    def set_frame_parameters(self, settings_index: int, frame_parameters: CameraFrameParameters) -> None:
        """Set the frame parameters with the settings index and fire the frame parameters changed event.
        If the settings index matches the current settings index, call set current frame parameters.
        If the settings index matches the record settings index, call set record frame parameters.
        """
        assert 0 <= settings_index < len(self.modes)
        frame_parameters = copy.copy(frame_parameters)
        self.__settings[settings_index] = frame_parameters
        # update the local frame parameters
        if settings_index == self.__current_settings_index:
            self.set_current_frame_parameters(frame_parameters)
        if settings_index == len(self.modes) - 1:
            self.set_record_frame_parameters(frame_parameters)
        self.settings_changed_event.fire(self.__save_settings())
        self.frame_parameters_changed_event.fire(settings_index, frame_parameters)

    def get_frame_parameters(self, settings_index) -> CameraFrameParameters:
        """Get the frame parameters for the settings index."""
        return copy.copy(self.__settings[settings_index])

    def set_selected_profile_index(self, settings_index: int) -> None:
        """Set the current settings index.
        Call set current frame parameters if it changed.
        Fire profile changed event if it changed.
        """
        assert 0 <= settings_index < len(self.modes)
        if self.__current_settings_index != settings_index:
            self.__current_settings_index = settings_index
            # set current frame parameters
            self.set_current_frame_parameters(self.__settings[self.__current_settings_index])
            self.settings_changed_event.fire(self.__save_settings())
            self.profile_changed_event.fire(settings_index)

    @property
    def selected_profile_index(self) -> int:
        """Return the current settings index."""
        return self.__current_settings_index

    def get_mode(self) -> str:
        """Return the current mode (named version of current settings index)."""
        return self.modes[self.__current_settings_index]

    def set_mode(self, mode: str) -> None:
        """Set the current mode (named version of current settings index)."""
        self.set_selected_profile_index(self.modes.index(mode))


class CameraModule:

    def __init__(self, stem_controller_id: str, camera_device: Camera, camera_settings: CameraSettings):
        self.stem_controller_id = stem_controller_id
        self.camera_device = camera_device
        self.camera_settings = camera_settings
        self.priority = 20
        self.camera_panel_type = "orsay_camera_panel"


def run(instrument: ivg_inst.ivgInstrument):

    camera_device = Camera("4", "CheeTah", 'http://129.175.108.52:8080', False, instrument, "TimePix3", _("TimePix3"), "eels")
    #camera_device.camera_panel_type = "eels"
    camera_settings = CameraSettings("TimePix3")

    Registry.register_component(CameraModule("VG_Lum_controller", camera_device, camera_settings), {"camera_module"})