# standard libraries
import copy
import math
import ctypes
import gettext
import numpy
import threading
import typing
import time
import logging

# local libraries
from nion.utils import Registry
from nion.utils import Geometry
from nion.instrumentation import scan_base
from nion.instrumentation import stem_controller

from nionswift_plugin.IVG.scan.orsayscan import orsayScan, LOCKERFUNC, UNLOCKERFUNCA
from nionswift_plugin.IVG.scan.ConfigVGLumDialog import ConfigDialog

from nionswift_plugin.IVG import ivg_inst

_ = gettext.gettext


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


class Device:

    def __init__(self, instrument: ivg_inst.ivgInstrument):
        self.scan_device_id = "orsay_scan_device"
        self.scan_device_name = _("VG Lumiere")
        self.stem_controller_id = "VG_Lum_controller"
        self.__channels = self.__get_channels()
        self.__frame = None
        self.__frame_number = 0
        self.__instrument = instrument
        self.__sizez = 2
        self.__probe_position = (0, 0)
        self.__rotation = 0.
        self.__is_scanning = False
        self.on_device_state_changed = None
        self.__profiles = self.__get_initial_profiles()
        self.__frame_parameters = copy.deepcopy(self.__profiles[0])
        self.flyback_pixels = 2
        self.__buffer = list()

        self.orsayscan = orsayScan(1, vg=True)
        self.spimscan = orsayScan(2, self.orsayscan.orsayscan, vg=True)

        self.orsayscan.SetInputs([1, 0])

        self.has_data_event = threading.Event()

        self.fnlock = LOCKERFUNC(self.__data_locker)
        self.orsayscan.registerLocker(self.fnlock)
        self.fnunlock = UNLOCKERFUNCA(self.__data_unlockerA)
        self.orsayscan.registerUnlockerA(self.fnunlock)

        self.orsayscan.setScanScale(0, 5.0, 5.0)

        ######

        self.pixel_time = 0.5
        self.field_of_view = 4000
        self.orsayscan.SetProbeAt(0, 0)
        self.__spim_pixels = 0
        self.subscan_status = True
        self.__spim = False

        self.p0 = 512
        self.p1 = 512
        self.p2 = 0
        self.p3 = 512
        self.p4 = 0
        self.p5 = 512
        self.Image_area = [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5]

        ######

        self.scan = self.orsayscan

    def close(self):
        pass

    def stop(self) -> None:
        """Stop acquiring."""
        pass

    def set_idle_position_by_percentage(self, x: float, y: float) -> None:
        """Set the idle position as a percentage of the last used frame parameters."""
        pass

    def cancel(self) -> None:
        """Cancel acquisition (immediate)."""
        self.orsayscan.stopImaging(True)
        self.__is_scanning = False

    def __get_channels(self) -> typing.List[Channel]:
        return [Channel(0, "ADF", True), Channel(1, "BF", True)]

    def __get_initial_profiles(self) -> typing.List[scan_base.ScanFrameParameters]:
        profiles = list()
        profiles.append(scan_base.ScanFrameParameters({"size": (512, 512), "pixel_time_us": 0.5, "fov_nm": 4000.}))
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

    def set_frame_parameters(self, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Called just before and during acquisition.
        Device should use these parameters for new acquisition; and update to these parameters during acquisition.
        """
        self.__frame_parameters = copy.deepcopy(frame_parameters)
        if self.field_of_view != frame_parameters['fov_nm']: self.field_of_view = frame_parameters['fov_nm']
        if self.pixel_time != frame_parameters['pixel_time_us']: self.pixel_time = frame_parameters['pixel_time_us']

        if self.scan_rotation != frame_parameters['rotation_rad']:
            self.scan_rotation = frame_parameters['rotation_rad']

        if frame_parameters['subscan_pixel_size']:
            self.subscan_status = True
            self.p0, self.p1 = frame_parameters['size']
            self.p2 = int(
                frame_parameters['subscan_fractional_center'][1] * self.p0 - frame_parameters['subscan_pixel_size'][
                    1] / 2)
            self.p4 = int(
                frame_parameters['subscan_fractional_center'][0] * self.p1 - frame_parameters['subscan_pixel_size'][
                    0] / 2)
            self.p3 = self.p2 + frame_parameters['subscan_pixel_size'][1]
            self.p5 = self.p4 + frame_parameters['subscan_pixel_size'][0]
            self.Image_area = [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5]
        else:
            if self.subscan_status or (self.Image_area[0], self.Image_area[1]) != frame_parameters['size']:
                self.p0, self.p1 = frame_parameters['size']
                self.p2, self.p4 = 0, 0
                self.p3, self.p5 = self.p0, self.p1
                self.Image_area = [self.p0, self.p1, 0, self.p3, 0, self.p5]
                self.subscan_status = False

    def save_frame_parameters(self) -> None:
        """Called when shutting down. Save frame parameters to persistent storage."""
        pass

    def start_frame(self, is_continuous: bool) -> int:
        """Start acquiring. Return the frame number."""
        if not self.__is_scanning:
            self.__buffer = list()
            self.__start_next_frame()

            if not self.__spim: self.__is_scanning = self.orsayscan.startImaging(0, 1)

            if self.__is_scanning: print('Acquisition Started')
        return self.__frame_number

    def __start_next_frame(self):
        frame_parameters = copy.deepcopy(self.__frame_parameters)
        self.__scan_context = stem_controller.ScanContext()
        channels = [copy.deepcopy(channel) for channel in self.__channels if channel.enabled]  # channel enabled is here
        size = Geometry.IntSize.make(
            frame_parameters.subscan_pixel_size if frame_parameters.subscan_pixel_size else frame_parameters.size)
        for channel in channels:
            channel.data = numpy.zeros(tuple(size), numpy.float32)
        self.__frame_number += 1
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

        # gotit = self.has_data_event.wait(5.0) #this is problably related to the call function that is always running but everything worked without it so i commented

        if self.__frame is None:
            self.__start_next_frame()

        current_frame = self.__frame  # this is from Frame Class defined above
        assert current_frame is not None
        data_elements = list()

        for channel in current_frame.channels:  # At the end of the day this uses channel_id, which is a 0, 1 saying which channel is which
            data_element = dict()
            if not self.__spim:
                data_array = self.imagedata[channel.channel_id * (self.__scan_area[1]):(channel.channel_id + 1) * (
                self.__scan_area[1]),
                             0: (self.__scan_area[0])].astype(numpy.float32)
                if self.subscan_status:  # Marcel programs returns 0 pixels without the sub scan region so i just crop
                    data_array = data_array[self.p4:self.p5, self.p2:self.p3]
                data_element["data"] = data_array
                properties = current_frame.frame_parameters.as_dict()
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                data_element["properties"] = properties
                if data_array is not None:
                    data_elements.append(data_element)

            else:
                data_array = self.imagedata[(channel.channel_id) * (self.__spim_pixels):(channel.channel_id + 1) * (
                    self.__spim_pixels),
                             0: (self.__spim_pixels)].astype(numpy.float32)
                if self.subscan_status:  # Marcel programs returns 0 pixels without the sub scan region so i just crop
                    data_array = data_array[self.p4:self.p5, self.p2:self.p3]
                data_element["data"] = data_array
                properties = current_frame.frame_parameters.as_dict()
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                data_element["properties"] = properties
                if data_array is not None:
                    data_elements.append(data_element)

        self.has_data_event.clear()

        current_frame.complete = True
        if current_frame.complete:
            self.__frame = None

        # return data_elements, complete, bad_frame, sub_area, frame_number, pixels_to_skip
        return data_elements, True, False, ((0, 0), data_array.shape), None, 0

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
        self.__pixeltime = value / 1e6
        self.orsayscan.pixelTime = self.__pixeltime

    @property
    def scan_rotation(self):
        return self.__rotation

    @scan_rotation.setter
    def scan_rotation(self, value):
        self.__rotation = value
        self.orsayscan.setScanRotation(self.__rotation)

    @property
    def Image_area(self):
        return self.__scan_area

    @Image_area.setter
    def Image_area(self, value):
        self.__scan_area = value
        self.orsayscan.setImageArea(self.__scan_area[0], self.__scan_area[1], self.__scan_area[2], self.__scan_area[3],
                                    self.__scan_area[4], self.__scan_area[5])
        self.imagedata = numpy.empty((self.__sizez * (self.__scan_area[0]), (self.__scan_area[1])), dtype=numpy.int16)
        self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)

    @property
    def probe_pos(self):
        return self.__probe_position

    @probe_pos.setter
    def probe_pos(self, value):
        self.__probe_position = value
        px, py = round(self.__probe_position[0] * self.__scan_area[0]), round(
            self.__probe_position[1] * self.__scan_area[1])
        self.orsayscan.SetProbeAt(py, px)

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

    @property
    def set_spim(self):
        return self.__spim

    @set_spim.setter
    def set_spim(self, value):
        self.__spim = value

        if self.__spim:
            if self.__is_scanning:
                self.orsayscan.stopImaging(True)
                self.__is_scanning = False
                logging.info('***SCAN***: Imaging was running. Turning it off...')

            logging.info(f'Spim using {self.spimscan.getImageArea()} pixels and {self.spimscan.GetFieldSize()} FOV')
            logging.info(
                f'Imaging using {self.orsayscan.getImageArea()} pixels and {self.orsayscan.GetFieldSize()} FOV')
            self.spimscan.setScanClock(2)
            self.__is_scanning = self.spimscan.startSpim(0, 1)

        else:
            logging.info('***SCAN***: Spim is done. Handling it..')
            self.spimscan.stopImaging(True)
            #self.__is_scanning = False
            self.__is_scanning = self.orsayscan.startImaging(0, 1)

    @property
    def set_spim_pixels(self):
        return self.__spim_pixels

    @set_spim_pixels.setter
    def set_spim_pixels(self, value):
        self.__spim_pixels = value
        self.spimscan.setImageArea(value, value, self.__scan_area[2], self.__scan_area[3], self.__scan_area[4],
                                   self.__scan_area[5])

    def __data_locker(self, gene, datatype, sx, sy, sz):
        sx[0] = self.__scan_area[0]
        sy[0] = self.__scan_area[1]
        sz[0] = self.__sizez
        datatype[0] = self.__sizez
        return self.imagedata_ptr.value

    def __data_unlocker(self, gene, newdata):
        self.has_data_event.set()

    def __data_unlockerA(self, gene, newdata, imagenb, rect):
        if newdata:
            self.__frame_number = imagenb
            self.has_data_event.set()

    def show_configuration_dialog(self, api_broker) -> None:
        """Open settings dialog, if any."""
        api = api_broker.get_api(version="1", ui_version="1")
        document_controller = api.application.document_controllers[0]._document_controller
        myConfig = ConfigDialog(document_controller)


def run(instrument: ivg_inst.ivgInstrument):
    scan_device = Device(instrument)
    component_types = {"scan_device"}  # the set of component types that this component represents
    Registry.register_component(scan_device, component_types)
