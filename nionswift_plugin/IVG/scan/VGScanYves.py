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
from json import load as json_load
from json import dump as json_dump
import os

# local libraries
from nion.utils import Registry
from nion.utils import Geometry
from nion.instrumentation import scan_base
from nion.instrumentation import camera_base
from nion.instrumentation import stem_controller
from nion.swift.model import HardwareSource

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
        self.__frame = None
        self.__frame_number = 0
        self.__line_number = 0
        self.__instrument = instrument
        self.__sizez = 2
        self.__probe_position = [0, 0]
        self.__probe_position_pixels = [0, 0]
        self.__rotation = 0.
        self.__is_scanning = False
        self.on_device_state_changed = None
        self.orsayscan = orsayScan(1, vg=True)
        self.spimscan = orsayScan(2, self.orsayscan.orsayscan, vg=True)

        #list all inputs
        totalinputs = self.orsayscan.getInputsCount()
        self.dinputs = dict()
        for index in range(totalinputs):
            prop = self.orsayscan.getInputProperties(index)
            self.dinputs[index] = [prop, False]
        self.usedinputs = list()
        self.__scan_size = self.orsayscan.getImageSize()
        self.__isSpim = False
        self.__spim_time_changed_event_listener = None
        self.__eels_mode_at_spim_start = None
        #def update_spim_time(frame_parameters):
        #    print(f"orsayscan: camera setting changed")

        self.__eelscamera = None
        # camera are not registered yet.
        # cameras = Registry.get_components_by_type("camera_module")
        # if cameras is not None:
        #     for cam in cameras:
        #         camera_type = cam.camera_device.camera_type
        #         if camera_type == "eels":
        #             self.__eelscamera = cam.camera_device
        #             self.__spim_time_changed_event_listener = cam.camera_settings.current_frame_parameters_changed_event.listen(self.__update_spim_time)
        #
        __inputs = self.orsayscan.GetInputs()
        self.__used_inputs = [[0, False, self.dinputs[0][0]],
                         [1, False, self.dinputs[1][0]],
                         [2, False, self.dinputs[2][0]],
                         [3, False, self.dinputs[3][0]],
                         #[4, False, self.dinputs[4][0]],
                         #[5, False, self.dinputs[5][0]],
                         [6, False, self.dinputs[6][0]],
                         [7, False, self.dinputs[7][0]],
                         [100, False,  [0, 0, "eels", 100]],
                         [200, False,  [0, 0, "spim_eels_spectrum", 200]],
                         [101, False,  [0, 0, "cl", 101]],
                         [201, False,  [0, 0, "spim_cl_spectrum", 201]]]

        def make_inputs_table(profile_index):
            for inp in __inputs[1]:
                for k in self.usedinputs[profile_index]:
                    if k[0] == inp:
                        k[1] = True

        self.__profiles = self.__get_initial_profiles()
        self.__currentprofileindex = 0
        # self.profiles = self.__profiles
        self.__channels = self.__get_channels()
        self.__frame_parameters = copy.deepcopy(self.__profiles[0])
        self.flyback_pixels = 0
        self.__buffer = list()
        self.__acquisition_stop_request = False

        self.orsayscan.SetInputs([1, 0])
        self.spimscan.SetInputs([1, 0])

        self.has_data_event = threading.Event()

        self.data_locker_function = LOCKERFUNC(self.__data_locker)
        self.orsayscan.registerLocker(self.data_locker_function)
        self.data_unlocker_function = UNLOCKERFUNCA(self.__data_unlockerA)
        self.orsayscan.registerUnlockerA(self.data_unlocker_function)

        self.orsayscan.setScanScale(0, 5.0, 5.0)

        ######

        self.pixel_time = 0.5
        self.field_of_view = 4000
        self.orsayscan.SetProbeAt(0, 0)
        self.__spim_pixels = (0, 0)
        self.subscan_status = True
        self.__spim = False

        self.p0 = 512
        self.p1 = 512
        self.p2 = 0
        self.p3 = 512
        self.p4 = 0
        self.p5 = 512
        self.Image_area = [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5]
        self.orsayscan.setScanRotation(35.0)

        #Set HADF and BF initial gain values
        self.orsayscan.SetPMT(1, 2200)
        self.orsayscan.SetPMT(0, 2200)

        ######

        self.scan = self.orsayscan
        self.__last_time = time.time()

    def close(self):
        if self.__spim_time_changed_event_listener is not None:
            self.__spim_time_changed_event_listener.close()
        self.orsayscan.close()

    def __update_spim_time(self, frame_parameters):
        if self.__currentprofileindex == 2:
            print(f"orsayscan: camera setting changed")

    def stop(self) -> None:
        """Stop acquiring at end f frame."""
        if self.__isSpim:
            # force immediate stop un fix is found
            self.spimscan.stopImaging(True)
            self.eels_camera.acquire_synchronized_end()
            self.__is_scanning = False
        else:
            self.orsayscan.stopImaging(False)
        self.__acquisition_stop_request = True

    def set_idle_position_by_percentage(self, x: float, y: float) -> None:
        """Set the idle position as a percentage of the last used frame parameters."""
        pass

    def cancel(self) -> None:
        """Cancel acquisition (immediate)."""
        if self.__isSpim:
            self.spimscan.stopImaging(True)
            self.eels_camera.acquire_synchronized_end()
        else:
            self.orsayscan.stopImaging(True)
        self.__is_scanning = False

    def __get_channels(self) -> typing.List[Channel]:
        return list(Channel(i, self.usedinputs[self.__currentprofileindex][i][2][2],\
                            self.__profiles[self.__currentprofileindex].channels[i])\
                    for i in range(len(self.__profiles[self.__currentprofileindex].channels)))

    def __get_initial_profiles(self) -> typing.List[scan_base.ScanFrameParameters]:
        def make_channels(input_list):
            return list(input_list[ch][1] for ch in range(len(input_list)))

        config_file = os.environ['ALLUSERSPROFILE'] + "\\Nion\\Nion Swift\\Orsay_scan_profiles.json"
        profiles = list()
        try:
            with open(config_file) as fp:
                profiles_dict = json_load(fp)
                pr = 0
                for prof in profiles_dict:
                    value = profiles_dict[prof]
                    self.usedinputs.append(value["inputs"])
                    # make_inputs_table(pr)
                    profiles.append(scan_base.ScanFrameParameters({"name": prof, "size": value["size"], "pixel_time_us": value["pixel_time_us"],
                                                                  "channels":make_channels(self.usedinputs[pr])}))
                    pr = pr+1
        except Exception as e:
            self.usedinputs.clear()
            self.usedinputs.append([[0, False, self.dinputs[0][0]],
                                    [1, False, self.dinputs[1][0]],
                                    [2, False, self.dinputs[2][0]],
                                    [3, False, self.dinputs[3][0]]])
            self.usedinputs.append([[0, False, self.dinputs[0][0]],
                                    [1, False, self.dinputs[1][0]],
                                    [6, False, self.dinputs[6][0]],
                                    [7, False, self.dinputs[7][0]]])
            self.usedinputs.append([[0, False, self.dinputs[0][0]],
                                    [1, False, self.dinputs[1][0]],
                                   [100, False, [0, 0, "eels", 100]]])
            self.usedinputs.append([[0, False, self.dinputs[0][0]],
                                    [1, False, self.dinputs[1][0]],
                                   [101, False, [0, 0, "eire", 101]]])
            self.usedinputs.append([[0, False, self.dinputs[0][0]],
                                    [1, False, self.dinputs[1][0]],
                                   [102, False, [0, 0, "dpc", 102]]])
            # for lp in range(0, len(self.usedinputs)):
            #     make_inputs_table(lp)
            profiles.append(scan_base.ScanFrameParameters({"name": _("Focus"),
                                                                  "size": (512, 512),
                                                                  "pixel_time_us": 0.2,
                                                                  "channels":make_channels(self.usedinputs[0])}))
            profiles.append(scan_base.ScanFrameParameters({"name": _("Photo"),
                                                                  "size": (1024, 1024),
                                                                  "pixel_time_us": 2,
                                                                  "channels":make_channels(self.usedinputs[1])}))
            profiles.append(scan_base.ScanFrameParameters({"name": _("Spim-eels"),
                                                                  "size": (64, 64),
                                                                  "pixel_time_us": 1000,
                                                                  "channels":make_channels(self.usedinputs[2])}))
            profiles.append(scan_base.ScanFrameParameters({"name": _("Spim-cl"),
                                                                  "size": (100, 100),
                                                                  "pixel_time_us": 2000,
                                                                  "channels":make_channels(self.usedinputs[3])}))
            profiles.append(scan_base.ScanFrameParameters({"name": _("dpc"),
                                                                  "size": (200, 200),
                                                                  "pixel_time_us": 100,
                                                                  "channels":make_channels(self.usedinputs[4])}))
            profiles_dict = dict()
            for pr in range(0, len(profiles)):
                profiles_dict[profiles[pr]["name"]] = {"size": profiles[pr]["size"],
                                                              "pixel_time_us": profiles[pr]["pixel_time_us"],
                                                              "inputs": self.usedinputs[pr]}
            with open(config_file, "w") as fp:
                json_dump(profiles_dict, fp, skipkeys=True, indent=4)
        return profiles

    @property
    def profile_index(self):
        return self.__currentprofileindex

    @profile_index.setter
    def profile_index(self, value):
        self.__currentprofileindex = value
        self.__channels = self.__get_channels()

    def get_initial_profiles(self):
        return self.__get_initial_profiles()

    def get_profile_frame_parameters(self, profile_index: int) -> scan_base.ScanFrameParameters:
        return copy.deepcopy(self.__profiles[profile_index])

    def set_profile_frame_parameters(self, profile_index: int, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Set the acquisition parameters for the give profile_index (0, 1, 2)."""
        self.__profiles[profile_index] = copy.deepcopy(frame_parameters)

    @property
    def eels_camera(self) -> camera_base.CameraHardwareSource:
        if self.__eelscamera is not None:
            return self.__eelscamera
        for hardware_source in HardwareSource.HardwareSourceManager().hardware_sources:
            if hardware_source.features.get("is_eels_camera"):
                self.__eelscamera = hardware_source
                break

        # camera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_kuro")

        def spim_time_changed(name, *args, **kwargs):
            if name == "exposure_ms":
                print(f"eels listener: New camera exposure")

        if self.__eelscamera is not None:
            self.__spim_time_changed_event_listener = self.__eelscamera.camera.frame_parameter_changed_event.listen(spim_time_changed)
        return self.__eelscamera

    def get_all_channel_name(self, channel_index: int) -> str:
        return self.__used_inputs[channel_index][2][2]

    def get_channel_name(self, channel_index: int) -> str:
        res = None
        if channel_index < len(self.__channels):
            res = self.__channels[channel_index].name
            # res = self.usedinputs[self.__currentprofileindex][channel_index][2][2]
        return res

    def get_input_index(self, channel_index :int) -> int:
        subscan = False
        lg = len(self.__channels)
        if channel_index < lg:
            value = channel_index
        else:
            value = channel_index - lg
            subscan = True
        return self.usedinputs[self.__currentprofileindex][value][0], subscan

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
            self.__instrument.is_subscan_f=[True, frame_parameters['subscan_pixel_size'][1]/self.p0, frame_parameters['subscan_pixel_size'][0]/self.p1]
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
                self.__instrument.is_subscan_f=[False, 1, 1]

    def save_frame_parameters(self) -> None:
        """Called when shutting down. Save frame parameters to persistent storage."""
        pass

    def start_frame(self, is_continuous: bool) -> int:
        """Start acquiring. Return the frame number."""
        # if not self.__is_scanning:
        #     self.__buffer = list()
        #     self.__start_next_frame()
        #
        #     if not self.__spim:
        #         self.imagedata = numpy.empty((self.__sizez * (self.__scan_area[0]), (self.__scan_area[1])), dtype=numpy.int16)
        #         self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
        #         self.__is_scanning = self.orsayscan.startImaging(0, 1)
        #
        #     if self.__is_scanning: print('Acquisition Started')
        # return self.__frame_number
        self.__acquisition_stop_request = False
        scan = self.orsayscan
        if not self.is_scanning:
            __inputs = []
            self.__isSpim = False

            pos = 0
            #for l in self.__frame_parameters.channels:
            for channel in self.__channels:
                if channel.enabled:
                    input_index, subscan = self.get_input_index(channel.channel_id)
                    isSpimChannel = input_index >= 100
                    if not isSpimChannel:
                        __inputs.append(input_index)
                    self.__isSpim |= isSpimChannel
                pos = pos + 1
            lg = len(__inputs)
            #
            # si le nombre d'entrée est plus grand que 1, il doit être pair!
            # limitation du firmware.
            #
            if self.__isSpim:
                scan = self.spimscan
                scan.setImageArea(self.__scan_area[0], self.__scan_area[1], self.__scan_area[2],
                                  self.__scan_area[3], self.__scan_area[4],
                                  self.__scan_area[5])
            if lg > 0:
                if lg % 2:
                    __inputs.append(6)
                nb, actual_inputs = scan.GetInputs()
                if (nb != len(__inputs)) or any(i!=j for i,j in zip(actual_inputs, __inputs)):
                    scan.SetInputs(__inputs)
            self.__scan_size = scan.getImageSize()
            self.__sizez = scan.GetInputs()[0]
            if self.__sizez % 2:
                self.__sizez += 1
            self.imagedata = numpy.empty((self.__sizez * self.__scan_size[1], self.__scan_size[0]), dtype = numpy.int16)
            self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
            self.__angle = 0
            # scan.setScanRotation(self.__angle)

            scan_shape = (self.__scan_size[1], self.__scan_size[0])
            if self.__isSpim:
                if self.eels_camera is not None:
                    orsaycamera = self.eels_camera.camera
                    settings = orsaycamera.current_camera_settings
                    scan.setScanClock(2)
                    if hasattr(settings, "acquisition_mode"):
                        self.__eels_mode_at_spim_start = settings["acquisition_mode"]
                        settings["acquisition_mode"] = "Spim"
                        orsaycamera.set_frame_parameters(settings)
                    if hasattr(settings, "simulated") and settings["simulated"]:
                        exp_read_out = orsaycamera.readoutTime
                        exp_read_out = exp_read_out + settings.exposure_ms/1000
                        scan.pixelTime = exp_read_out-0.000001
                        scan.clock_simulation_time = exp_read_out
                    else:
                        scan.clock_simulation_time = 0
                        scan.pixelTime = orsaycamera.settings.exposure_ms/1000
                    self.__is_scanning = scan.startSpim(0,1)
                    self.eels_camera.acquire_synchronized_begin(settings, scan_shape)
            else:
                self.__is_scanning = scan.startImaging(0, 1)
            self.__frame_number = 0
            self.__last_time = time.time()

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

        gotit = self.has_data_event.wait(5.0)

        if self.__frame is None:
            self.__start_next_frame()

        current_frame = self.__frame  # this is from Frame Class defined above
        assert current_frame is not None
        data_elements = list()

        # At the end of the day this uses channel_id, which is a 0, 1 saying which channel is which
        sub_area = None
        channel_index = 0
        for channel in self.__channels:
            if channel.enabled and self.__is_scanning:
                data_element = dict()
                properties = current_frame.frame_parameters.as_dict()
                properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                properties["channel_id"] = channel.channel_id
                for key, value in self.__profiles[self.__currentprofileindex].as_dict().items():
                    properties[key] = value
                input_index, subscan = self.get_input_index(channel.channel_id)
                if input_index < 100:
                # if not self.__spim:
                    data_array = self.imagedata[channel_index * (self.__scan_area[1]):(channel_index + 1) * (
                    self.__scan_area[1]),
                                 0: (self.__scan_area[0])].astype(numpy.float32)
                    if self.subscan_status:  # Marcel programs returns 0 pixels without the sub scan region so i just crop
                        data_array = data_array[self.p4:self.p5, self.p2:self.p3]
                    data_element["data"] = data_array
                    sub_area = ((0, 0), data_array.shape)
                    properties['sub_area'] = sub_area
                    data_element["properties"] = properties
                    if data_array is not None:
                        data_elements.append(data_element)

                elif self.__isSpim:
                    partial_data_info = self.eels_camera.acquire_synchronized_continue(update_period=1.0)
                    if not partial_data_info.is_canceled:
                        sub_area = ((0, 0, 0), (data_array.shape[1], data_array.shape[0], 1))
                        properties['sub_area'] = sub_area
                        data_element["data"] = partial_data_info.xdata.data
                        properties['sub_area'] = sub_area
                        data_element["properties"] = properties
                        _name = self.usedinputs[self.__currentprofileindex][channel_index][2][2]
                        # if _name == "eels":
                        #     self.__eelscamera.camera.update_spatial_calibrations_a(data_element)
                        #     self.__eelscamera.camera.update_intensity_calibrations_a(data_element)
                        # else:
                        data_element["spatial_calibrations"] = (
                            {"offset": 0, "scale": 1, "units": "eV"},
                        )
                        data_element["collection_dimension_count"] = 1
                        data_element["datum_dimension_count"] = 1
                        data_elements.append(data_element)
                        if partial_data_info.is_complete:
                            hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                                self.scan_device_id)
                            hardware_source.stop_playing()
                channel_index = channel_index + 1

        # else:
                #     data_array = self.imagedata[channel.channel_id * (self.__scan_area[1]):channel.channel_id * (
                #         self.__scan_area[1]) + self.__spim_pixels[1],
                #                  0: (self.__spim_pixels[0])].astype(numpy.float32)
                #     #data_array = self.imagedata.astype(numpy.float32)
                #     #if self.subscan_status:  # Marcel programs returns 0 pixels without the sub scan region so i just crop
                #     #    data_array = data_array[self.p4:self.p5, self.p2:self.p3]
                #     data_element["data"] = data_array
                #     properties = current_frame.frame_parameters.as_dict()
                #     properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
                #     properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
                #     properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
                #     properties["channel_id"] = channel.channel_id
                #     data_element["properties"] = properties
                #     if data_array is not None:
                #         data_elements.append(data_element)

        complete = True
        bad_frame = False
        self.has_data_event.clear()

        if self.__line_number == self.__scan_size[1]:
            current_frame.complete = True
            sub_area = ((pixels_to_skip // self.__scan_size[1], 0), (self.__scan_size[1], self.__scan_size[0]))
            pixels_to_skip = 0
        else:
            sub_area = ((pixels_to_skip // self.__scan_size[1], 0), (self.__line_number, self.__scan_size[0]))
            pixels_to_skip = self.__line_number * self.__scan_size[1]

        if current_frame.complete:
            self.__frame = None
        return data_elements, complete, bad_frame, sub_area, self.__frame_number, pixels_to_skip

    #This one is called in scan_base
    def prepare_synchronized_scan(self, scan_frame_parameters: scan_base.ScanFrameParameters, *, camera_exposure_ms, **kwargs) -> None:
        scan_frame_parameters["pixel_time_us"] = min(5120000, int(1000 * camera_exposure_ms * 0.75))
        scan_frame_parameters["external_clock_wait_time_ms"] = 20000 # int(camera_frame_parameters["exposure_ms"] * 1.5)
        scan_frame_parameters["external_clock_mode"] = 1
        pass


    def set_channel_enabled(self, channel_index: int, enabled: bool) -> bool:
        assert 0 <= channel_index < self.channel_count
        self.__channels[channel_index].enabled = enabled
        self.__profiles[self.__currentprofileindex].channels[channel_index] = enabled
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
        self.__rotation = value*180/numpy.pi
        self.orsayscan.setScanRotation(self.__rotation)

    @property
    def Image_area(self):
        return self.__scan_area

    @Image_area.setter
    def Image_area(self, value):
        self.__scan_area = value
        self.orsayscan.setImageArea(self.__scan_area[0], self.__scan_area[1], self.__scan_area[2], self.__scan_area[3],
                                    self.__scan_area[4], self.__scan_area[5])
        # better done at start when analysing channels
        # self.__sizez = sum(self.channels_enabled)
        # # orsay scan requires an even number of channel space if greater > 1
        # if (self.__sizez != 1) and (self.__sizez % 2 != 0):
        #     self.__sizez += 1
        # self.imagedata = numpy.empty((self.__sizez * (self.__scan_area[0]), (self.__scan_area[1])), dtype=numpy.int16)
        # self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)

    @property
    def probe_pos(self):
        return self.__probe_position

    @probe_pos.setter
    def probe_pos(self, value):
        self.__probe_position = value
        #This is a very strange behavior of geometry class. Very misleading. Value is a tuple like
        #(x=0.1, y=0.3) but value[0] gives y value while value[1] gives x value. You can check here
        #print(f'value is {value} and first is {value[0]}. Second is {value[1]}')
        #If you using this func, please call it with (y, x)
        px, py = round(self.__probe_position[1] * self.__scan_area[1]), round(
            self.__probe_position[0] * self.__scan_area[0])
        self.__probe_position_pixels = [px, py]
        self.orsayscan.SetProbeAt(px, py)

    @property
    def current_frame_parameters(self) -> scan_base.ScanFrameParameters:
        return self.__frame_parameters

    @property
    def is_scanning(self) -> bool:
        self.__is_scanning = self.orsayscan.getImagingKind() != 0
        return self.__is_scanning

    @property
    def all_channel_count(self):
        return len(self.__used_inputs)

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

        #self.__is_scanning is false for spim. This allows us a better control of data flow. See first loop
        #condition in read_partial.

        if self.__spim:
            if self.is_scanning:
                self.orsayscan.stopImaging(True)
                self.__is_scanning = False
                logging.info('***SCAN***: Imaging was running. Turning it off...')

            if self.__instrument.spim_trigger_f==0:
                self.spimscan.setScanClock(2)
                logging.info(f'***SCAN***: EELS Spim')
            elif self.__instrument.spim_trigger_f==1:
                self.spimscan.setScanClock(4)
                logging.info(f'***SCAN***: Cathodoluminescence Spim')

            self.imagedata = numpy.empty((self.__sizez * (self.__scan_area[0]), (self.__scan_area[1])), dtype=numpy.int16)
            self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
            self.spimscan.startSpim(0, 1)

        else:
            logging.info('***SCAN***: Spim is done. Handling...')
            self.spimscan.stopImaging(True)
            self.__is_scanning = False

            pmts=[]
            for counter, value in enumerate(self.channels_enabled):
                if value: pmts.append(counter)
            self.__instrument.warn_Scan_instrument_spim_over(self.imagedata, self.__spim_pixels, pmts)


    @property
    def set_spim_pixels(self):
        return self.__spim_pixels

    @set_spim_pixels.setter
    def set_spim_pixels(self, value):
        if value:
            self.__spim_pixels = value
            self.spimscan.setImageArea(self.__spim_pixels[0], self.__spim_pixels[1], self.__scan_area[2], self.__scan_area[3], self.__scan_area[4],
                                   self.__scan_area[5])

    def __data_locker(self, gene, datatype, sx, sy, sz):
        sx[0] = self.__scan_area[0]
        sy[0] = self.__scan_area[1]
        sz[0] = self.__sizez
        datatype[0] = 2
        return self.imagedata_ptr.value

    def __data_unlockerA(self, gene, newdata, imagenb, rect):
        if newdata:
            self.__frame_number = imagenb
            self.has_data_event.set()
            self.__line_number = rect[1] + rect[3]

    def show_configuration_dialog(self, api_broker) -> None:
        from json import load as json_load
        from json import dump as json_dump
        import os
        """Open settings dialog, if any."""
        api = api_broker.get_api(version="1", ui_version="1")
        document_controller = api.application.document_controllers[0]._document_controller
        myConfig = ConfigDialog(document_controller)


def run(instrument: ivg_inst.ivgInstrument):
    scan_device = Device(instrument)
    component_types = {"scan_device"}  # the set of component types that this component represents
    Registry.register_component(scan_device, component_types)


