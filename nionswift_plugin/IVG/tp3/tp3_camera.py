# standard libraries
import copy
import socket
import gettext
import numpy
import typing
import logging
import time

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

    def __init__(self, camera_id: str, camera_type: str, camera_name: str, instrument: ivg_inst.ivgInstrument):
        self.camera_id = camera_id
        self.camera_type = camera_type
        self.camera_name = camera_name

        self.__frame_number = 0
        self.__is_playing = False
        self.__readout_area = (0, 0, 256, 1024)
        self.__lastImage = None

        self.__tp3 = tp3func.TimePix3('http://129.175.108.52:8080')

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
        det_config = self.__tp3.get_config()
        self.__tp3.acq_init(det_config, 1, frame_parameters['exposure_ms'], 1)
        self.__tp3.set_destination()

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

    def stop_live(self) -> None:
        """Stop live acquisition."""
        self.__is_playing = False
        logging.info('***TP3***: Stopping acquisition...')
        self.__tp3.finish_acq_simple()


    def acquire_image(self):
        """Acquire the most recent data."""
        start = time.time()
        self.__frame_number += 1

        self.__tp3.start_acq_simple()
        acq_time = time.time()
        logging.info(f'Acq is over. Total time is {acq_time - start}.')
        data = self.acquire_single_frame(port = 8088)
        client_time = time.time()
        logging.info(f'Client got it. Total time is {client_time - acq_time}.')

        if data[0]:
            image_data=data[1]
            self.__tp3.finish_acq_simple()
        else:
            #image_data=self.__lastImage
            image_data = numpy.random.randn(256, 1024)

        collection_dimensions = 0
        datum_dimensions = 2

        properties = dict()
        properties["frame_number"] = self.__frame_number
        calibration_controls = copy.deepcopy(self.calibration_controls)

        return {"data": image_data, "collection_dimension_count": collection_dimensions,
                "datum_dimension_count": datum_dimensions,
                "properties": properties}

    def acquire_single_frame(self, port=8088):

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.1)
        ip = socket.gethostbyname('129.175.108.52')
        adress = (ip, port)
        try:
            client.connect(adress)
        except ConnectionRefusedError:
            return (False, None)

        cam_properties = dict()
        frame_data = b''
        success = False

        def check_string_value(header, prop):
            start_index = header.index(prop)
            end_index = start_index + len(prop)
            begin_value = header.index(':', end_index, len(header)) + 1
            end_value = header.index(',', end_index, len(header))
            return float(header[begin_value:end_value])

        while True:
            data = client.recv(8192)
            if len(data) <= 0:
                client.close()
                success = True
                break
            elif b'timeAtFrame' in data:
                header = data[:-1].decode()
                for properties in ['timeAtFrame', 'frameNumber', 'dataSize', 'width']:
                    cam_properties[properties] = (check_string_value(header, properties))
                end_header = header.index('}')
                frame_data = data[end_header+2:]
            else:
                try:
                    frame_data += data
                except Exception as e:
                    logging.info(f'Exception is {e}')
                if len(frame_data) > cam_properties['dataSize']:
                    print(len(frame_data))
                    frame_data = numpy.array(frame_data[:-1])
                    frame_int = numpy.frombuffer(frame_data, dtype=numpy.int8)
                    frame_int = numpy.reshape(frame_int, (256, 1024))
                    self.__lastImage = frame_int

        return (success, self.__lastImage)


class CameraFrameParameters(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
        self.exposure_ms = self.get("exposure_ms", 125)
        self.binning = self.get("binning", 1)
        self.processing = self.get("processing")
        self.integration_count = self.get("integration_count")

    def __copy__(self):
        return self.__class__(copy.copy(dict(self)))

    def __deepcopy__(self, memo):
        deepcopy = self.__class__(copy.deepcopy(dict(self)))
        memo[id(self)] = deepcopy
        return deepcopy

    def as_dict(self):
        return {
            "exposure_ms": self.exposure_ms,
            "binning": self.binning,
            "processing": self.processing,
            "integration_count": self.integration_count,
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
        self.modes = ["Run", "Tune", "Snap"]

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
        #self.camera_panel_type = "tp3_camera_panel"


def run(instrument: ivg_inst.ivgInstrument):

    camera_device = Camera("TimePix3", "eels", _("TimePix3"), instrument)
    camera_device.camera_panel_type = "eels"
    camera_settings = CameraSettings("TimePix3")

    Registry.register_component(CameraModule("VG_Lum_controller", camera_device, camera_settings), {"camera_module"})