# standard libraries
import copy
import socket
import gettext
import numpy
import threading
import time
import typing
import pathlib
import requests
import json
import logging

# local libraries
from nion.utils import Event
from nion.utils import Registry

from nionswift_plugin.IVG import ivg_inst

# other plug-ins
from nion.instrumentation import camera_base

_ = gettext.gettext


class Camera(camera_base.CameraDevice):
    """Implement a camera device."""

    def __init__(self, camera_id: str, camera_type: str, camera_name: str, instrument: ivg_inst.ivgInstrument):
        self.camera_id = camera_id
        self.camera_type = camera_type
        self.camera_name = camera_name

        self.__serverURL = 'http://129.175.108.52:8080'
        self.__frame_number = 0
        self.__is_playing = False
        self.__readout_area = (0, 0, 256, 1024)
        self.__lastImage = None

        initial_status_code = self.tp3x_status_code()
        if initial_status_code==200: logging.info('***TP3***: Timepix has initialized correctly.')
        else: logging.info('***TP3***: Problem initializing Timepix')

        #Loading bpc and dacs
        bpcFile = '/home/asi/load_files/tpx3-demo.bpc'
        dacsFile = '/home/asi/load_files/tpx3-demo.dacs'
        self.tp3x_cam_init(bpcFile, dacsFile)

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
        det_config = self.tp3x_get_config()
        self.tp3x_acq_init(det_config, 1, frame_parameters['exposure_ms'], 10)

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
            print('camera starting')

    def stop_live(self) -> None:
        """Stop live acquisition."""
        self.__is_playing = False
        print('stoping camera')


    def acquire_image(self):
        """Acquire the most recent data."""
        self.__frame_number += 1


        self.tp3x_set_destination()
        threading.Thread(target=self.tp3x_acq_single, args=(),).start()
        data = self.acquire_single_frame()

        collection_dimensions = 0
        datum_dimensions = 2

        properties = dict()
        properties["frame_number"] = self.__frame_number
        calibration_controls = copy.deepcopy(self.calibration_controls)

        return {"data": data, "collection_dimension_count": collection_dimensions,
                "datum_dimension_count": datum_dimensions,
                "properties": properties}

    def acquire_single_frame(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setblocking(True)
        ip = socket.gethostbyname('129.175.108.52')
        port = 8088
        adress = (ip, port)
        client.connect(adress)

        cam_properties = dict()
        header = ''
        frame_data = b''

        done = False

        def check_string_value(header, prop):
            start_index = header.index(prop)
            end_index = start_index + len(prop)
            begin_value = header.index(':', end_index, len(header)) + 1
            end_value = header.index(',', end_index, len(header))
            return float(header[begin_value:end_value])

        while not done:
            data = client.recv(2048)
            if len(data) <= 0:
                done = True
            elif b'timeAtFrame' in data:
                header = data[:-1].decode()
                for properties in ['timeAtFrame', 'frameNumber', 'dataSize', 'width']:
                    cam_properties[properties] = (check_string_value(header, properties))
                frame_data = b''
                #print(cam_properties)
            else:
                frame_data += data
                if len(frame_data) >= cam_properties['dataSize']:
                    if frame_data[-1] == 10:
                        frame_data = numpy.array(frame_data[:-1])
                        frame_int = numpy.frombuffer(frame_data, dtype=numpy.int8)
                        frame_int = numpy.reshape(frame_int, (256, 1024))
                        self.__lastImage = frame_int
                        done = True

        return self.__lastImage

    def tp3x_status_code(self):
        try:
            resp = requests.get(url=self.__serverURL)
        except requests.exceptions.RequestException as e:  # Exceptions handling example
            return -1
        status_code = resp.status_code
        return status_code

    def tpx3_dashboard(self):
        resp = requests.get(url=self.__serverURL + '/dashboard')
        data = resp.text
        dashboard = json.loads(data)
        return dashboard

    def tp3x_cam_init(self, bpc_file, dacs_file):
        resp = requests.get(url = self.__serverURL + '/config/load?format=pixelconfig&file=' + bpc_file)
        data = resp.text
        logging.info(f'***TP3***: Response of loading binary pixel configuration file: ' + data)

        resp = requests.get(url=self.__serverURL + '/config/load?format=dacs&file=' + dacs_file)
        data=resp.text
        logging.info(f'***TP3***: Response of loading dacs file: ' + data)

    def tp3x_get_config(self):
        resp = requests.get(url=self.__serverURL + '/detector/config')
        data = resp.text
        detectorConfig = json.loads(data)
        return detectorConfig

    def tp3x_acq_init(self, detector_config, ntrig=1, shutter_open_ms=490, shutter_closed_ms=10):
        detector_config["nTriggers"] = ntrig
        detector_config["TriggerMode"] = "AUTOTRIGSTART_TIMERSTOP"
        detector_config["TriggerPeriod"] = (shutter_open_ms + shutter_closed_ms) / 1000
        detector_config["ExposureTime"] = shutter_open_ms / 1000

        resp = requests.put(url=self.__serverURL + '/detector/config', data=json.dumps(detector_config))
        data = resp.text
        #logging.info('Response of updating Detector Configuration: ' + data)

    def tp3x_set_destination(self):
        destination = {
            "Raw": [{
                # URI to a folder where to place the raw files.
                # "Base": pathlib.Path(os.path.join(os.getcwd(), 'data')).as_uri(),
                "Base": 'file:///home/asi/load_files/data',
                # How to name the files for the various frames.
                "FilePattern": "raw%Hms_",
            }],
            "Image": [{
                # "Base": "tcp://129.175.108.52:8088",
                "Base": "tcp://localhost:8088",
                "Format": "jsonimage",
                "Mode": "count"
            }]
        }
        resp = requests.put(url=self.__serverURL + '/server/destination', data=json.dumps(destination))
        data = resp.text
        #logging.info('Response of uploading the Destination Configuration to SERVAL : ' + data)


    def tp3x_acq_single(self):
        resp = requests.get(url=self.__serverURL + '/measurement/start')
        data = resp.text
        #logging.info('Response of acquisition start: ' + data)
        taking_data = True
        while taking_data:
            dashboard = json.loads(requests.get(url=self.__serverURL + '/dashboard').text)
            #logging.info(dashboard)
            if dashboard["Measurement"]["Status"] == "DA_IDLE":
                taking_data = False
                resp = requests.get(url=self.__serverURL + '/measurement/stop')
                data = resp.text
                #logging.info('Acquisition was stopped with response: ' + data)


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


def run(instrument: ivg_inst.ivgInstrument):

    camera_device = Camera("tp3", "eels", _("tp3_camera"), instrument)
    camera_device.camera_panel_type = "eels"
    camera_settings = CameraSettings("tp3")

    Registry.register_component(CameraModule("VG_Lum_controller", camera_device, camera_settings), {"camera_module"})