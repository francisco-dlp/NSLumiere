# standard libraries
import copy, math, ctypes, gettext, numpy, threading, typing, logging, os, json, time

# local libraries
from nion.utils import Registry
from nion.utils import Geometry
from nion.instrumentation import scan_base
from nion.instrumentation import stem_controller
from nion.swift.model import HardwareSource

from nionswift_plugin.IVG.scan.orsayscan import orsayScan, LOCKERFUNC, UNLOCKERFUNCA
from nionswift_plugin.IVG.scan.ConfigVGLumDialog import ConfigDialog
from nionswift_plugin.IVG import ivg_inst
from ...aux_files import read_data

_ = gettext.gettext

set_file = read_data.FileManager('global_settings')
ORSAY_SCAN_IS_VG = set_file.settings["OrsayInstrument"]["orsay_scan"]["IS_VG"]
ORSAY_SCAN_EFM03 = set_file.settings["OrsayInstrument"]["orsay_scan"]["EFM03"]
CROP_SUBSCAN = True
DEBUG = False

# set the calibrations for this image. does not touch metadata.
def test_update_scan_data_element(data_element, scan_frame_parameters, data_shape, channel_name, channel_id,
                             scan_properties):
    scan_properties = copy.deepcopy(scan_properties)
    pixel_time_us = float(scan_properties["pixel_time_us"])
    line_time_us = float(scan_properties["line_time_us"]) if "line_time_us" in scan_properties else pixel_time_us * \
                                                                                                    data_shape[1]
    center_x_nm = float(scan_properties.get("center_x_nm", 0.0))
    center_y_nm = float(scan_properties.get("center_y_nm", 0.0))
    fov_nm = float(scan_frame_parameters.fov_nm)  # context fov_nm, not actual fov_nm returned from low level
    if scan_frame_parameters.size[0] > scan_frame_parameters.size[1]:
        fractional_size = scan_frame_parameters.subscan_fractional_size[
            0] if scan_frame_parameters.subscan_fractional_size else 1.0
        pixel_size = scan_frame_parameters.subscan_pixel_size[0] if scan_frame_parameters.subscan_pixel_size else \
        scan_frame_parameters.size[0]
        pixel_size_nm = fov_nm * fractional_size / pixel_size
    else:
        fractional_size = scan_frame_parameters.subscan_fractional_size[
            1] if scan_frame_parameters.subscan_fractional_size else 1.0
        pixel_size = scan_frame_parameters.subscan_pixel_size[1] if scan_frame_parameters.subscan_pixel_size else \
        scan_frame_parameters.size[1]
        pixel_size_nm = fov_nm * fractional_size / pixel_size
    data_element["title"] = channel_name
    data_element["version"] = 1
    data_element["channel_id"] = channel_id  # needed to match to the channel
    data_element["channel_name"] = channel_name  # needed to match to the channel
    if scan_properties.get("calibration_style") == "time":
        data_element["spatial_calibrations"] = (
            {"offset": 0.0, "scale": line_time_us / 1E6, "units": "s"},
            {"offset": 0.0, "scale": pixel_time_us / 1E6, "units": "s"}
        )
    else:
        data_element["spatial_calibrations"] = [
            {"offset": -center_y_nm - pixel_size_nm * data_shape[0] * 0.5, "scale": pixel_size_nm, "units": "nm"},
            {"offset": -center_x_nm - pixel_size_nm * data_shape[1] * 0.5, "scale": pixel_size_nm, "units": "nm"}
        ]
        if len(data_shape) == 3: #3D acquisitions. This is typically a hyperspectral image.
            eels_dispersion = float(scan_properties.get("eels_dispersion", 1.0))
            eels_offset = float(scan_properties.get("eels_offset", 0.0))
            data_element["spatial_calibrations"].append(
                {"offset": eels_offset, "scale": eels_dispersion, "units": "eV"}
            )
scan_base.update_scan_data_element = test_update_scan_data_element

class Orsay_Data():
    def __init__(self):
        self.__s16 = 2
        self.__s32 = 3
        self.__uns16 = 6
        self.__uns32 = 7
        self.__float = 11
        self.__real = 12

    def numpy_to_orsay_type(self, array: numpy.array):
        orsay_type = self.__float
        if array.dtype == numpy.double:
            orsay_type = self.__real
        elif array.dtype == numpy.int16:
            orsay_type = self.__s16
        elif array.dtype == numpy.int32:
            orsay_type = self.__s32
        elif array.dtype == numpy.uint16:
            orsay_type = self.__uns16
        elif array.dtype == numpy.uint32:
            orsay_type = self.__uns32
        return orsay_type

class Channel:
    def __init__(self, channel_id: int, name: str, enabled: bool):
        self.channel_id = channel_id
        self.name = name
        self.enabled = enabled
        self.data = None

class Frame:
    def __init__(self, frame_number: int, channels: typing.List[Channel],
                 frame_parameters: scan_base.ScanFrameParameters):
        self.frame_number = frame_number
        self.channels = channels
        self.frame_parameters = frame_parameters
        self.complete = False
        self.bad = False
        self.data_count = 0
        self.start_time = time.time()
        self.scan_data = None

class Device(scan_base.ScanDevice):
    def __init__(self, instrument):
        self.scan_device_id = "orsay_scan_device"
        self.scan_device_is_secondary = True
        self.scan_device_name = _("OrsayScan")
        self.__channels = self.__get_channels()
        self.__frame = None
        self.__frame_number = 0
        self.__scan_list = False
        self.__instrument = instrument
        self.__sizez = 2
        self.__probe_position = [0, 0]
        self.__probe_position_pixels = [0, 0]
        self.__rotation = 0.
        self.__is_scanning = False
        self.__is_tpx3_running = False
        self.on_device_state_changed = None
        self.__profiles = self.__get_initial_profiles()
        self.__frame_parameters = copy.deepcopy(self.__profiles[0])
        self.flyback_pixels = 2
        self.__buffer = list()
        self.__sequence_buffer_size = 0
        self.__timeout = 0.25
        self.__last_time = time.time()
        self.__view_buffer_size = 20
        self.bottom_blanker = 0

        self.orsayscan = orsayScan(1, vg=bool(ORSAY_SCAN_IS_VG), efm03=bool(ORSAY_SCAN_EFM03))
        self.spimscan = orsayScan(2, self.orsayscan.orsayscan, vg=bool(ORSAY_SCAN_IS_VG), efm03=bool(ORSAY_SCAN_EFM03))
        self.__orsay_data_type = Orsay_Data()

        #Depending on the microscopes we use different input channels
        input_channels = [0, 1] if bool(ORSAY_SCAN_IS_VG) else [3, 2]
        self.orsayscan.SetInputs(input_channels)
        self.spimscan.SetInputs(input_channels)

        self.has_data_event = threading.Event()

        self.fnlock = LOCKERFUNC(self.__data_locker)
        self.orsayscan.registerLocker(self.fnlock)
        self.fnunlock = UNLOCKERFUNCA(self.__data_unlockerA)
        self.orsayscan.registerUnlockerA(self.fnunlock)

        ######

        self.pixel_time = 0.5
        self.field_of_view = 25
        self.orsayscan.SetProbeAt(0, 0)
        self.__spim_pixels = (0, 0)
        self.__line_number = 0
        self.subscan_status = True
        self.__spim = False

        self.__tpx3_spim = False
        self.__tpx3_4d = False
        self.__tpx3_data = None
        self.__tpx3_camera = None
        self.__tpx3_calib = dict()
        self.__tpx3_frameStop = 0

        self.orsayscan.Image_area = [512, 512, 0, 512, 0, 512]
        self.spimscan.Image_area = [128, 128, 0, 512, 0, 512]
        self.scan_rotation = 0.0
        self.orsayscan.setScanScale(0, 5.0, 5.0)

        #Set HADF and BF initial gain values
        self.orsayscan.SetPMT(1, 2200)
        self.orsayscan.SetPMT(0, 2200)

        ######

        self.scan = self.orsayscan

    def timeout(function):
        def wrapper(self, *args):
            if time.time() - self.__last_time > self.__timeout:
                function(self, *args)
                self.__last_time = time.time()
        return wrapper

    def close(self):
        pass

    def stop(self) -> None:
        """Stop acquiring."""
        self.__spim = False
        if self.__is_tpx3_running:
            self.__is_tpx3_running = False
            self.stop_timepix3()
        if self.__is_scanning:
            self.orsayscan.stopImaging(True)
            self.spimscan.stopImaging(True)
            self.__is_scanning = False

    def set_idle_position_by_percentage(self, x: float, y: float) -> None:
        """Set the idle position as a percentage of the last used frame parameters."""
        pass

    def cancel(self) -> None:
        """Cancel acquisition (immediate)."""
        self.__spim = False
        if self.__is_tpx3_running:
            self.__is_tpx3_running = False
            self.stop_timepix3()
        if self.__is_scanning:
            self.orsayscan.stopImaging(False)
            self.spimscan.stopImaging(True)
            self.__is_scanning = False

    def __get_channels(self) -> typing.List[Channel]:
        channels = [Channel(0, "ADF", ORSAY_SCAN_IS_VG), Channel(1, "BF", False)]
        return channels

    def __get_initial_profiles(self) -> typing.List[scan_base.ScanFrameParameters]:
        profiles = list()
        profiles.append(scan_base.ScanFrameParameters({"size": (512, 512), "pixel_time_us": 0.5, "fov_nm": 400., "rotation_rad": 0.393}))
        profiles.append(scan_base.ScanFrameParameters({"size": (128, 128), "pixel_time_us": 1, "fov_nm": 100.}))
        profiles.append(scan_base.ScanFrameParameters({"size": (512, 512), "pixel_time_us": 1, "fov_nm": 100.}))
        return profiles

    def get_profile_frame_parameters(self, profile_index: int) -> scan_base.ScanFrameParameters:
        return copy.deepcopy(self.__profiles[profile_index])

    def set_profile_frame_parameters(self, profile_index: int, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Set the acquisition parameters for the give profile_index (0, 1, 2)."""
        self.__profiles[profile_index] = copy.deepcopy(frame_parameters)

    def get_channel_name(self, channel_index: int) -> str:
        return self.__channels[channel_index].name

    @timeout
    def set_frame_parameters(self, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Called just before and during acquisition.
        Device should use these parameters for new acquisition; and update to these parameters during acquisition.
        """
        self.__frame_parameters = copy.deepcopy(frame_parameters)
        if self.field_of_view != frame_parameters.fov_nm:
            self.field_of_view = frame_parameters.fov_nm
        if self.pixel_time != frame_parameters.pixel_time_us:
            self.pixel_time = frame_parameters.pixel_time_us
        if self.scan_rotation != frame_parameters.rotation_rad:
            self.scan_rotation = frame_parameters.rotation_rad

        if self.__spim:
            scan = self.spimscan
        else:
            scan = self.orsayscan

        p00, p10 = scan.getImageSize()

        if frame_parameters.subscan_pixel_size:
            self.subscan_status = True
            if self.__spim:
                p0, p1 = frame_parameters.subscan_pixel_size.width, frame_parameters.subscan_pixel_size.height
                # roi is taken from tuning settings.
                p2 = self.orsayscan.Image_area[2]
                p3 = self.orsayscan.Image_area[3]
                p4 = self.orsayscan.Image_area[4]
                p5 = self.orsayscan.Image_area[5]
            else:
                p0, p1 = frame_parameters.size.width, frame_parameters.size.height
                p2 = int(
                    frame_parameters.subscan_fractional_center.x * p0 - frame_parameters.subscan_pixel_size.width / 2)
                p4 = int(
                    frame_parameters.subscan_fractional_center.y * p1 - frame_parameters.subscan_pixel_size.height / 2)
                p3 = p2 + int(frame_parameters.subscan_pixel_size.width)
                p5 = p4 + int(frame_parameters.subscan_pixel_size.height)
            scan.Image_area = [p0, p1, p2, p3, p4, p5]
        else:
            self.subscan_status = False
            p0, p1 = frame_parameters.size.width, frame_parameters.size.height
            if self.__spim:
                # roi is taken from tuning settings.
                p3 = self.orsayscan.Image_area[3]
                p5 = self.orsayscan.Image_area[5]
            else:
                p0, p1 = frame_parameters.size.width, frame_parameters.size.height
                p3, p5 = p0, p1
            scan.Image_area = [p0, p1, 0, p3, 0, p5]

        if p0 != p00 or p1 != p10:
            self.__scan_size = (p0, p1)
            self.__sizez = scan.GetInputs()[0]
            size_summed = self.__sizez * self.__scan_size[1] * self.__scan_size[0]
            self.imagedata = numpy.zeros(size_summed, dtype=int)
            self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)

        if DEBUG:
            print(f'Is spim: {self.__spim}. Value set is {scan.Image_area}')

    def save_frame_parameters(self) -> None:
        """Called when shutting down. Save frame parameters to persistent storage."""
        pass

    def prepare_timepix3(self, channel_type):
        self.__tpx3_camera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            "orsay_camera_timepix3")
        if channel_type == "TPX3":
            self.__tpx3_spim = self.__tpx3_camera.camera.camera.StartSpimFromScan()
            if self.__tpx3_spim: #True if successful
                self.__tpx3_calib["dispersion"] = self.__instrument.TryGetVal("EELS_TV_eVperpixel")[1]
                self.__tpx3_calib["offset"] = self.__instrument.TryGetVal("ZLPtare")[1]
                self.__tpx3_camera.camera.camera._TimePix3__isReady.wait(5.0)
                self.__tpx3_data = self.__tpx3_camera.camera.camera.create_spimimage() #Getting the reference
                time.sleep(0.5) #Timepix has already a socket connected. Wait until it is definitely reading data
        elif channel_type == "4D_TPX3":
            self.__tpx3_4d = self.__tpx3_camera.camera.camera.Start4DFromScan()
            if self.__tpx3_4d:  # True if successful
                self.__tpx3_calib["dispersion"] = 1 #4d channels
                self.__tpx3_calib["offset"] = 0 #Starts at 0
                self.__tpx3_camera.camera.camera._TimePix3__isReady.wait(5.0)
                self.__tpx3_data = self.__tpx3_camera.camera.camera.create_4dimage() #Getting the reference
                time.sleep(0.5)  # Timepix has already a socket connected. Wait until it is definitely reading data

    def stop_timepix3(self):
        if self.__tpx3_spim or self.__tpx3_4d: #only stop if this was on
            self.__tpx3_camera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            "orsay_camera_timepix3")
            self.__tpx3_camera.camera.camera.stopSpim(True)
            self.__tpx3_spim = False
            self.__tpx3_4d = False

    def no_prepare_timepix3(self):
        self.__tpx3_data = None

    def start_frame(self, is_continuous: bool) -> int:
        """Start acquiring. Return the frame number."""
        if not self.__is_scanning:
            self.__buffer = list()
            self.__start_next_frame()

            logging.info(f"***SCAN***: Starting acquisition. Spim is {self.__spim}")

            # Picking between scans
            if self.__spim:
                self.spimscan.setScanClock(4)
                scan = self.spimscan
            else:
                scan = self.orsayscan

            if DEBUG:
                print(f'Sizez is {self.__sizez} and scan_size is {self.__scan_size}. Image area: {scan.Image_area} and'
                      f' {self.__spim_pixels} and the shape of imagedata is {self.imagedata.shape}')

            should_start = False
            if not self.__spim:
                for channel in self.__channels:
                    if channel.name == 'TPX3' or channel.name == "4D_TPX3":
                        if channel.enabled:
                            self.__is_tpx3_running = True
                            self.prepare_timepix3(channel.name)
                    if channel.name == "ADF" or channel.name == "BF":
                        if channel.enabled:
                            should_start = True
                        #else:
                        #    self.no_prepare_timepix3()
                #Scan must be started after timepix3 so we are ready for receiving TDC's
                if should_start: self.__is_scanning = self.orsayscan.startImaging(0, 1)
            else:
                self.__is_scanning = self.spimscan.startSpim(0, 1)

            assert ((self.__tpx3_spim & self.__tpx3_4d) == False) #One of them is allowed
            logging.info(f'**SCAN***: Acquisition Started is {self.__is_scanning}.')
        return self.__frame_number

    def __start_next_frame(self):
        frame_parameters = copy.deepcopy(self.__frame_parameters)
        self.__scan_context = stem_controller.ScanContext()
        channels = [copy.deepcopy(channel) for channel in self.__channels if channel.enabled]  # channel enabled is here
        size = Geometry.IntSize.make(
            frame_parameters.subscan_pixel_size if frame_parameters.subscan_pixel_size else frame_parameters.size)
        for channel in channels:
            channel.data = numpy.zeros(tuple(size), numpy.float32)
        self.__frame_number += 1 #This is updated in the self.__frame_number
        self.__frame = Frame(self.__frame_number, channels, frame_parameters)

    def read_partial(self, frame_number, pixels_to_skip) -> (typing.Sequence[dict], bool, bool, tuple, int, int):
        """Read or continue reading a frame.
        The `frame_number` may be None, in which case a new frame should be read.
        The `frame_number` otherwise specifies which frame to continue reading.
        The `pixels_to_skip` specifies where to start reading the frame, if it is a continuation.
        Return values should be a list of dict's (one for each active channel) containing two keys: 'data' and
        'properties' (see below), followed by a boolean indicating whether the frame is complete, a boolean indicating
        whether the frame was bad, a tuple of the form (top, left), (height, width) indicating the valid sub-area
        of the data, the frame number, and the pixels to skip next time around if the frame is not complete.
        The 'data' keys in the list of dict's should contain a ndarray with the size of the full acquisition and each
        ndarray should be the same size. The 'properties' keys are dicts which must contain the frame parameters and
        a 'channel_id' indicating the index of the channel (may be an int or float).
        """

        gotit = self.has_data_event.wait(1.0)

        if self.__frame is None:
            self.__start_next_frame()

        current_frame = self.__frame  # this is from Frame Class defined above
        assert current_frame is not None
        frame_parameters = current_frame.frame_parameters
        scan_area = self.spimscan.Image_area if self.__spim else self.orsayscan.Image_area

        #If its spim, the line_number is given by the sampling. If its not the spim, the value of the roi is used.
        if (self.__line_number == scan_area[1] and self.__spim) or \
                ((self.__line_number == scan_area[5] and not self.__spim)):
            current_frame.complete = True
            sub_area = ((0, 0), (self.__scan_size[1], self.__scan_size[0]))
            pixels_to_skip = 0
        else:
            sub_area = ((0, 0), (self.__line_number, self.__scan_size[0]))
            pixels_to_skip = self.__line_number * self.__scan_size[1]

        if DEBUG:
            print(f'Line number is {self.__line_number} and scan area is {scan_area}.'
                  f'Complete: {current_frame.complete}. sub_area is {sub_area}.')

        data_elements = list()
        sxy = scan_area[1] * scan_area[0]
        if CROP_SUBSCAN and not self.__spim:
            offsety = [scan_area[2], scan_area[3]]
            offsetx = [scan_area[4], scan_area[5]]
        else:
            offsety = [0, scan_area[0]]
            offsetx = [0, scan_area[1]]


        for channel in current_frame.channels:
            data_element = dict()

            #Timepix3 Spim channel
            if channel.name == 'TPX3':
                #if self.__frame_number % 10 == 0:
                data_array = self.__tpx3_data
                data_element["data"] = data_array
                properties = current_frame.frame_parameters.as_dict()
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                properties["eels_dispersion"] = self.__tpx3_calib["dispersion"]
                properties["eels_offset"] = self.__tpx3_calib["offset"]
                data_element["properties"] = properties
                if data_array is not None:
                    data_elements.append(data_element)

            elif channel.name == '4D_TPX3':
                #if self.__frame_number % 10 == 0:
                data_array = self.__tpx3_data
                data_element["data"] = data_array
                properties = current_frame.frame_parameters.as_dict()
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                properties["eels_dispersion"] = self.__tpx3_calib["dispersion"]
                properties["eels_offset"] = self.__tpx3_calib["offset"]
                data_element["properties"] = properties
                if data_array is not None:
                    data_elements.append(data_element)
            else:
                data_array = self.imagedata[channel.channel_id * sxy: (channel.channel_id + 1) * sxy]
                data_array = data_array.reshape(scan_area[1], scan_area[0]).astype('float32')
                data_array = data_array[offsetx[0]:offsetx[1], offsety[0]:offsety[1]]
                data_element["data"] = data_array
                properties = current_frame.frame_parameters.as_dict()
                properties['sub_area'] = ((0, 0), data_array.shape)
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                data_element["properties"] = properties
                if data_array is not None:
                    data_elements.append(data_element)

        bad_frame = False
        self.has_data_event.clear()

        if current_frame.complete:
            if len(self.__buffer) > 0 and len(self.__buffer[-1]) != len(data_elements):
                self.__buffer = list()
            self.__buffer.append(data_elements)
            while len(self.__buffer) > self.__sequence_buffer_size + self.__view_buffer_size:
                del self.__buffer[self.__sequence_buffer_size]
        self.__frame = None

        #Stop by using the number of frames
        if self.__tpx3_spim and self.__tpx3_frameStop != 0 and self.__frame_number >= self.__tpx3_frameStop:
            logging.info(f"***SCAN***: Stopped frame acquisition by using the frame stop property. Total number"
                         f"of frames are {self.__frame_number}.")
            self.stop()

        return data_elements, current_frame.complete, bad_frame, sub_area, self.__frame_number, pixels_to_skip

    #This one is called in scan_base
    def prepare_synchronized_scan(self, scan_frame_parameters: scan_base.ScanFrameParameters, *, camera_exposure_ms, **kwargs) -> None:
        self.__spim = True

    def set_sequence_buffer_size(self, buffer_size: int) -> None:
        self.__sequence_buffer_size = buffer_size
        self.__buffer = list()

    def get_sequence_buffer_count(self) -> int:
        return len(self.__buffer)

    def pop_sequence_buffer_data(self) -> typing.List[typing.Dict[str, typing.Any]]:
        self.__sequence_buffer_size -= 1
        return self.__buffer.pop(0)

    def get_buffer_data(self, start: int, count: int) -> typing.List[typing.List[typing.Dict[str, typing.Any]]]:
        # print(f"get {start=} {count=} {len(self.__buffer)=}")
        # time.sleep(0.1)
        if start < 0:
            return self.__buffer[start: start + count if count < -start else None]
        else:
            return self.__buffer[start: start + count]

    def calculate_flyback_pixels(self, frame_parameters: scan_base.ScanFrameParameters) -> int:
        return 0

    def set_channel_enabled(self, channel_index: int, enabled: bool) -> bool:
        assert 0 <= channel_index < self.channel_count
        self.__channels[channel_index].enabled = enabled
        if not any(channel.enabled for channel in self.__channels):
            self.cancel()
        return True

    def set_scan_context_probe_position(self, scan_context: stem_controller.ScanContext,
                                        probe_position: Geometry.FloatPoint):
        if probe_position:
            self.probe_pos = probe_position

    @property
    def field_of_view(self):
        return self.__fov

    @field_of_view.setter
    def field_of_view(self, value):
        self.__fov = value / 1e9
        if self.__fov > 72 * 1e-6: self.__fov = 72. * 1e6
        self.orsayscan.SetFieldSize(self.__fov)
        self.__instrument.fov_change(self.__fov)

    @property
    def pixel_time(self):
        return self.__pixeltime

    @pixel_time.setter
    def pixel_time(self, value):
        self.__pixeltime = value
        self.orsayscan.pixelTime = self.__pixeltime / 1e6

    @property
    def scan_rotation(self):
        return self.__rotation

    @scan_rotation.setter
    def scan_rotation(self, value):
        self.__rotation = value*180/numpy.pi
        self.orsayscan.setScanRotation(self.__rotation)

    @property
    def probe_pos(self):
        return self.__probe_position

    @probe_pos.setter
    @timeout
    def probe_pos(self, value):
        self.__probe_position = value
        #This is a very strange behavior of geometry class. Very misleading. Value is a tuple like
        #(x=0.1, y=0.3) but value[0] gives y value while value[1] gives x value. You can check here
        #print(f'value is {value} and first is {value[0]}. Second is {value[1]}')
        #If you using this func, please call it with (y, x)
        px, py = round(self.__probe_position[1] * self.orsayscan.Image_area[1]), round(
            self.__probe_position[0] * self.orsayscan.Image_area[0])
        self.__probe_position_pixels = [px, py]
        self.orsayscan.SetProbeAt(px, py)

    @property
    def current_frame_parameters(self) -> scan_base.ScanFrameParameters:
        return self.__frame_parameters

    @property
    def is_scanning(self) -> bool:
        return self.__is_scanning

    @property
    def channel_count(self):
        return len(self.__channels)

    @property
    def channels_enabled(self) -> typing.Tuple[bool, ...]:
        return tuple(channel.enabled for channel in self.__channels)

    def __data_locker(self, gene, datatype, sx, sy, sz):
        if gene == 1:
            sx[0] = self.orsayscan.Image_area[0]
            sy[0] = self.orsayscan.Image_area[1]
        else:
            sx[0] = self.spimscan.Image_area[0]
            sy[0] = self.spimscan.Image_area[1]
        sz[0] = self.__sizez
        datatype[0] = self.__orsay_data_type.numpy_to_orsay_type(self.imagedata)
        return self.imagedata_ptr.value

    def __data_unlockerA(self, gene, newdata, imagenb, rect):
        if newdata:
            self.__frame_number = imagenb
            if self.__scan_list:
                # artificially give a line number from number of pixels
                self.__pixels = rect[0]
                if gene == 1:
                    self.__line_number = rect[0] / (self.orsayscan.Image_area[3] - self.orsayscan.Image_area[2])
                else:
                    self.__line_number = rect[0] / (self.spimscan.Image_area[3] - self.spimscan.Image_area[2])
            else:
                self.__line_number = rect[1] + rect[3]
            self.has_data_event.set()

def open_configuration_interface(api_broker) -> None:
    """Open settings dialog, if any."""
    api = api_broker.get_api(version="1", ui_version="1")
    document_controller = api.application.document_controllers[0]._document_controller
    ConfigDialog(document_controller)

class ScanModule(scan_base.ScanModule):
    def __init__(self, instrument: ivg_inst.ivgInstrument) -> None:
        self.stem_controller_id = instrument.instrument_id
        self.device = Device(instrument)
        setattr(self.device, "priority", 20)
        scan_modes = (
            scan_base.ScanSettingsMode(_("Fast"), "fast", scan_base.ScanFrameParameters(pixel_size=(256, 256), pixel_time_us=1, fov_nm=1000, rotation_rad=0.393)),
            scan_base.ScanSettingsMode(_("Slow"), "slow", scan_base.ScanFrameParameters(pixel_size=(512, 512), pixel_time_us=1, fov_nm=25)),
            scan_base.ScanSettingsMode(_("Record"), "record", scan_base.ScanFrameParameters(pixel_size=(1024, 1024), pixel_time_us=1, fov_nm=25))
        )
        self.settings = scan_base.ScanSettings(scan_modes, lambda d: scan_base.ScanFrameParameters(d), 0, 2,
                                               open_configuration_dialog_fn=open_configuration_interface)


def run(instrument: ivg_inst.ivgInstrument) -> None:
    Registry.register_component(ScanModule(instrument), {"scan_module"})

def stop() -> None:
    Registry.unregister_component(Registry.get_component("scan_module"), {"scan_module"})