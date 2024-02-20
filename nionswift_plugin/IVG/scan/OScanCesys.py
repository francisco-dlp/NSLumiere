# standard libraries
import copy, math, gettext, numpy, typing, time, threading, logging, os, sys, json

# local libraries
from nion.utils import Registry
from nion.utils import Geometry
from nion.utils import Event
from nion.instrumentation import scan_base, stem_controller
from nion.instrumentation import HardwareSource

from nionswift_plugin.IVG.scan.OScanCesysDialog import ConfigDialog
from FPGAControl import FPGAConfig
from ...aux_files import read_data

from .OScanCesysDialog import KERNEL_LIST, ACQUISITION_WINDOW, SCAN_MODES, IMAGE_VIEW_MODES

_ = gettext.gettext

set_file = read_data.FileManager('global_settings')
OPEN_SCAN_IS_VG = set_file.settings["OrsayInstrument"]["open_scan"]["IS_VG"]
OPEN_SCAN_EFM03 = set_file.settings["OrsayInstrument"]["open_scan"]["EFM03"]
OPEN_SCAN_BITSTREAM = set_file.settings["OrsayInstrument"]["open_scan"]["BITSTREAM_FILE"]
FILENAME_JSON = 'opscan_persistent_data.json'
DEBUG = False

def getlibname():
    if sys.platform.startswith('win'):
        libname = os.path.join(os.path.dirname(__file__), "../../aux_files/DLLs/")
    else:
        libname = os.path.join(os.path.dirname(__file__), "../../aux_files/DLLs/")
    return libname


class ArgumentController:
    def __init__(self):
        try:
            with open(FILENAME_JSON) as f:
                self.argument_controller = json.load(f)
        except FileNotFoundError:
            self.argument_controller = dict()
            with open(FILENAME_JSON, 'w') as f:
                json.dump(self.argument_controller, f)

    def get(self, keyname: str, value = None):
        return self.argument_controller.get(keyname, value)

    def keys(self):
        return self.argument_controller.keys()

    def update(self, **kwargs):
        self.argument_controller.update(**kwargs)
        self.write_to_json()

    def write_to_json(self):
        with open(FILENAME_JSON) as f:
            data = json.load(f)
        data.update(self.argument_controller)
        with open(FILENAME_JSON, 'w') as f:
            json.dump(data, f)

class ScanEngine:
    def __init__(self):
        self.property_changed_event = Event.Event()
        try:
            self.debug_io = None
            io_system = FPGAConfig.CesysDevice(getlibname().encode(),
                                               OPEN_SCAN_BITSTREAM)
            self.device = FPGAConfig.ScanDevice(io_system, 128, 128, 100, 0)
        except UnboundLocalError:
            self.debug_io = FPGAConfig.DebugClass()
            self.device = FPGAConfig.ScanDevice(self.debug_io, 128, 128, 100, 0)
            logging.warning(f'Could not found CESYS system connected. Entering in debug mode.')
        except:
            self.debug_io = FPGAConfig.DebugClass()
            self.device = FPGAConfig.ScanDevice(self.debug_io, 128, 128, 100, 0)
            logging.warning(f'Could not found the library libudk3-1.5.1.so. You should probably use '
                            f'export LD_LIBRARY_PATH='+getlibname())

        self.__x = None
        self.__y = None
        self.__pixel_ratio = None

        #Settings
        self.argument_controller = ArgumentController()

        for keys in self.argument_controller.keys():
            setattr(self, keys, getattr(self, keys))

        # setattr(self, 'imagedisplay', getattr(self, 'imagedisplay'))
        # setattr(self, 'imagedisplay_filter_intensity', getattr(self, 'imagedisplay_filter_intensity'))
        # self.adc_acquisition_mode = self.argument_controller.get('adc_acquisition_mode')
        # self.duty_cycle = self.argument_controller.get('duty_cycle')
        # self.dsp_filter = self.argument_controller.get('dsp_filter')
        # self.video_delay = self.argument_controller.get('video_delay')
        # self.pause_sampling = self.argument_controller.get('pause_sampling')
        # self.external_trigger = self.argument_controller.get('external_trigger')
        # self.flyback_us = self.argument_controller.get('flyback_us')
        # self.rastering_mode = self.argument_controller.get('rastering_mode')
        # self.mini_scan = self.argument_controller.get('mini_scan')
        # self.magboard_switches = self.argument_controller.get('magboard_switches')
        # self.offset_adc0 = self.argument_controller.get('offset_adc0')
        # self.offset_adc1 = self.argument_controller.get('offset_adc1')
        # self.offset_adc2 = self.argument_controller.get('offset_adc2')
        # self.offset_adc3 = self.argument_controller.get('offset_adc3')
        # self.multiblock0 = self.argument_controller.get('multiblock0')
        # self.multiblock1 = self.argument_controller.get('multiblock1')
        # self.multiblock2 = self.argument_controller.get('multiblock2')
        # self.multiblock3 = self.argument_controller.get('multiblock3')
        # self.mag_multiblock0 = self.argument_controller.get('mag_multiblock0')
        # self.mag_multiblock1 = self.argument_controller.get('mag_multiblock1')
        # self.mag_multiblock2 = self.argument_controller.get('mag_multiblock2')
        # self.mag_multiblock3  = self.argument_controller.get('mag_multiblock3')
        # self.mag_multiblock4 = self.argument_controller.get('mag_multiblock4')
        # self.mag_multiblock5 = self.argument_controller.get('mag_multiblock5')
        # self.lissajous_nx = self.argument_controller.get('lissajous_nx')
        # self.lissajous_ny = self.argument_controller.get('lissajous_ny')
        # self.lissajous_phase = self.argument_controller.get('lissajous_phase')
        # self.kernel_mode = self.argument_controller.get('kernel_mode')
        # self.given_pixel = self.argument_controller.get('given_pixel')
        # self.acquisition_cutoff = self.argument_controller.get('acquisition_cutoff')
        # self.acquisition_window = self.argument_controller.get('acquisition_window')
        # self.input1_mux = self.argument_controller.get('input1_mux')
        # self.input2_mux = self.argument_controller.get('input2_mux')
        # self.routex_mux = self.argument_controller.get('routex_mux')
        # self.routex_mux_intensity = self.argument_controller.get('routex_mux_intensity')
        # self.routex_mux_averages = self.argument_controller.get('routex_mux_averages')
        # self.routey_mux = self.argument_controller.get('routey_mux')
        # self.routey_mux_intensity = self.argument_controller.get('routey_mux_intensity')
        # self.routey_mux_averages = self.argument_controller.get('routey_mux_averages')
        # #O1TTL
        # self.output1_mux_type = self.argument_controller.get('mux_output_type')[0]
        # self.output1_mux_freq = self.argument_controller.get('mux_output_freq')[0]
        # self.output1_mux_input = self.argument_controller.get('mux_output_input')[0]
        # self.output1_mux_input_div = self.argument_controller.get('mux_output_input_div')[0]
        # self.output1_mux_delay = self.argument_controller.get('mux_output_delay')[0]
        # #O2TTL
        # self.output2_mux_type = self.argument_controller.get('mux_output_type')[1]
        # self.output2_mux_freq = self.argument_controller.get('mux_output_freq')[1]
        # self.output2_mux_input = self.argument_controller.get('mux_output_input')[1]
        # self.output2_mux_input_div = self.argument_controller.get('mux_output_input_div')[1]
        # self.output2_mux_delay = self.argument_controller.get('mux_output_delay')[1]
        # #O3TTL
        # self.output3_mux_type = self.argument_controller.get('mux_output_type')[2]
        # self.output3_mux_freq = self.argument_controller.get('mux_output_freq')[2]
        # self.output3_mux_input = self.argument_controller.get('mux_output_input')[2]
        # self.output3_mux_input_div = self.argument_controller.get('mux_output_input_div')[2]
        # self.output3_mux_delay = self.argument_controller.get('mux_output_delay')[2]
        # #O4TTL
        # self.output4_mux_type = self.argument_controller.get('mux_output_type')[3]
        # self.output4_mux_freq = self.argument_controller.get('mux_output_freq')[3]
        # self.output4_mux_input = self.argument_controller.get('mux_output_input')[3]
        # self.output4_mux_input_div = self.argument_controller.get('mux_output_input_div')[3]
        # self.output4_mux_delay = self.argument_controller.get('mux_output_delay')[3]
        # #EXT_TRIGGER
        # self.output5_mux_type = self.argument_controller.get('mux_output_type')[4]
        # self.output5_mux_freq = self.argument_controller.get('mux_output_freq')[4]
        # self.output5_mux_input = self.argument_controller.get('mux_output_input')[4]
        # self.output5_mux_input_div = self.argument_controller.get('mux_output_input_div')[4]
        # self.output5_mux_delay = self.argument_controller.get('mux_output_delay')[4]

        # self.imagedisplay = 0
        # self.imagedisplay_filter_intensity = 25
        # self.adc_acquisition_mode = 5
        # self.duty_cycle = 100
        # self.dsp_filter = 0
        # self.video_delay = 0
        # self.pause_sampling = False
        # self.external_trigger = 0
        # self.flyback_us = 0
        # self.rastering_mode = 0
        # self.mini_scan = 2
        # self.magboard_switches = '100100'
        # self.offset_adc0 = self.offset_adc1 = self.offset_adc2 = self.offset_adc3 = 0
        # self.multiblock0 = self.multiblock1 = self.multiblock2 = self.multiblock3 = 1.0
        # self.mag_multiblock0 = self.mag_multiblock1 = self.mag_multiblock2 = self.mag_multiblock3  = 1.0
        # self.mag_multiblock4 = self.mag_multiblock5 = 0.0
        # self.lissajous_nx = 190.8
        # self.lissajous_ny = 190.5
        # self.lissajous_phase = 0
        # self.kernel_mode = 0
        # self.given_pixel = 1
        # self.acquisition_cutoff = 500
        # self.acquisition_window = 2
        # self.input1_mux = 2
        # self.input2_mux = 3
        # self.routex_mux = 0
        # self.routex_mux_intensity = 0
        # self.routex_mux_averages = 0
        # self.routey_mux = 0
        # self.routey_mux_intensity = 0
        # self.routey_mux_averages = 0
        # #O1TTL
        # self.output1_mux_type = 1
        # self.output1_mux_freq = 1000
        # self.output1_mux_input = 0
        # self.output1_mux_input_div = 0
        # self.output1_mux_delay = 0
        # #O2TTL
        # self.output2_mux_type = 3
        # self.output2_mux_freq = 1000
        # self.output2_mux_input = 0
        # self.output2_mux_input_div = 0
        # self.output2_mux_delay = 0
        # #O3TTL
        # self.output3_mux_type = 0
        # self.output3_mux_freq = 1000
        # self.output3_mux_input = 0
        # self.output3_mux_input_div = 0
        # self.output3_mux_delay = 0
        # #O4TTL
        # self.output4_mux_type = 0
        # self.output4_mux_freq = 1000
        # self.output4_mux_input = 0
        # self.output4_mux_input_div = 0
        # self.output4_mux_delay = 0
        # #EXT_TRIGGER
        # self.output5_mux_type = 6
        # self.output5_mux_freq = 1000
        # self.output5_mux_input = 0
        # self.output5_mux_input_div = 0
        # self.output5_mux_delay = 0

    def receive_total_frame(self, channel: int):
        image = self.device.get_image(channel, imageType=IMAGE_VIEW_MODES[self.imagedisplay], low_pass_size=self.imagedisplay_filter_intensity)
        return image

    def set_frame_parameters(self, frame_parameters: scan_base.ScanFrameParameters):
        is_synchronized_scan = frame_parameters.get_parameter("external_clock_mode", 0)
        (y, x) = frame_parameters.as_dict()['pixel_size']
        pixel_time = frame_parameters.as_dict()['pixel_time_us']
        fov_nm = frame_parameters.as_dict()['fov_nm']
        rotation_rad = frame_parameters.as_dict().get('rotation_rad', 0.0)
        subscan_fractional_size = frame_parameters.as_dict().get('subscan_fractional_size')
        subscan_fractional_center = frame_parameters.as_dict().get('subscan_fractional_center')
        subscan_pixel_size = frame_parameters.as_dict().get('subscan_pixel_size')

        self.device.change_scan_parameters(x, y, pixel_time, self.flyback_us, fov_nm, is_synchronized_scan, SCAN_MODES[self.rastering_mode],
                                           rotation_rad = rotation_rad,
                                           lissajous_nx=self.lissajous_nx,
                                           lissajous_ny=self.lissajous_ny,
                                           lissajous_phase=self.lissajous_phase,
                                           subimages=self.mini_scan,
                                           kernelMode=KERNEL_LIST[self.kernel_mode],
                                           givenPixel=self.given_pixel,
                                           dutyCycle=self.duty_cycle,
                                           acquisitionCutoff=self.acquisition_cutoff,
                                           acquisitionWindow=self.acquisition_window,
                                           subscan_fractional_size=subscan_fractional_size,
                                           subscan_fractional_center=subscan_fractional_center,
                                           subscan_pixel_size=subscan_pixel_size
                                           )

    def set_probe_position(self, x, y):
        self.device.set_probe_position(x, y)

    @property
    def imagedisplay(self):
        if self.argument_controller.get('imagedisplay') == None:
            self.argument_controller.update(imagedisplay=0)  # default
        return self.argument_controller.get('imagedisplay')

    @imagedisplay.setter
    def imagedisplay(self, value):
        self.argument_controller.update(imagedisplay=int(value))

    @property
    def imagedisplay_filter_intensity(self):
        if self.argument_controller.get('imagedisplay_filter_intensity') == None:
            self.argument_controller.update(imagedisplay_filter_intensity=0)  # default
        return self.argument_controller.get('imagedisplay_filter_intensity')

    @imagedisplay_filter_intensity.setter
    def imagedisplay_filter_intensity(self, value):
        self.argument_controller.update(imagedisplay_filter_intensity=int(value))

    @property
    def flyback_us(self):
        if self.argument_controller.get('flyback_us') == None:
            self.argument_controller.update(flyback_us=0)  # default
        return self.argument_controller.get('flyback_us')

    @flyback_us.setter
    def flyback_us(self, value):
        self.argument_controller.update(flyback_us=int(value))

    @property
    def external_trigger(self):
        if self.argument_controller.get('external_trigger') == None:
            self.argument_controller.update(external_trigger=0)  # default
        return self.argument_controller.get('external_trigger')

    @external_trigger.setter
    def external_trigger(self, value):
        self.argument_controller.update(external_trigger=int(value))

    @property
    def duty_cycle(self):
        if self.argument_controller.get('duty_cycle') == None:
            self.argument_controller.update(duty_cycle=0)  # default
        return self.argument_controller.get('duty_cycle')

    @duty_cycle.setter
    def duty_cycle(self, value):
        self.argument_controller.update(duty_cycle=int(value))

    @property
    def dsp_filter(self):
        if self.argument_controller.get('dsp_filter') == None:
            self.argument_controller.update(dsp_filter=0)  # default
        return self.argument_controller.get('dsp_filter')

    @dsp_filter.setter
    def dsp_filter(self, value):
        self.argument_controller.update(dsp_filter=int(value))
        self.device.change_video_parameters(dsp_filter=self.argument_controller.get('dsp_filter'))

    @property
    def video_delay(self):
        if self.argument_controller.get('video_delay') == None:
            self.argument_controller.update(video_delay=0)  # default
        return self.argument_controller.get('video_delay')

    @video_delay.setter
    def video_delay(self, value):
        self.argument_controller.update(video_delay=int(value))
        self.device.change_video_parameters(video_delay=self.argument_controller.get('video_delay'))
        #If timepix3 is present, we should try to set the metadata of this value
        cam = HardwareSource.HardwareSourceManager()\
            .get_hardware_source_for_hardware_source_id("orsay_camera_timepix3")
        if cam is not None:
            cam.camera.camera.set_video_delay(value)


    @property
    def pause_sampling(self):
        if self.argument_controller.get('pause_sampling') == None:
            self.argument_controller.update(pause_sampling=0)  # default
        return self.argument_controller.get('pause_sampling')

    @pause_sampling.setter
    def pause_sampling(self, value):
        self.argument_controller.update(pause_sampling=int(value))
        self.device.change_video_parameters(pause_sampling=self.argument_controller.get('pause_sampling'))


    @property
    def adc_acquisition_mode(self):
        if self.argument_controller.get('adc_acquisition_mode') == None:
            self.argument_controller.update(adc_acquisition_mode=0)  # default
        return self.argument_controller.get('adc_acquisition_mode')

    @adc_acquisition_mode.setter
    def adc_acquisition_mode(self, value):
        self.argument_controller.update(adc_acquisition_mode=int(value))
        self.device.change_video_parameters(adc_acquisition_mode=self.argument_controller.get('adc_acquisition_mode'))

    @property
    def rastering_mode(self):
        if self.argument_controller.get('rastering_mode') == None:
            self.argument_controller.update(rastering_mode=0)  # default
        return self.argument_controller.get('rastering_mode')

    @rastering_mode.setter
    def rastering_mode(self, value):
        self.argument_controller.update(rastering_mode=int(value))

    @property
    def mini_scan(self):
        if self.argument_controller.get('mini_scan') == None:
            self.argument_controller.update(mini_scan=0)  # default
        return self.argument_controller.get('mini_scan')

    @mini_scan.setter
    def mini_scan(self, value):
        self.argument_controller.update(mini_scan=int(value))

    @property
    def lissajous_nx(self):
        if self.argument_controller.get('lissajous_nx') == None:
            self.argument_controller.update(lissajous_nx=0)  # default
        return self.argument_controller.get('lissajous_nx')

    @lissajous_nx.setter
    def lissajous_nx(self, value):
        self.argument_controller.update(lissajous_nx=float(value))

    @property
    def lissajous_ny(self):
        if self.argument_controller.get('lissajous_ny') == None:
            self.argument_controller.update(lissajous_ny=0)  # default
        return self.argument_controller.get('lissajous_ny')

    @lissajous_ny.setter
    def lissajous_ny(self, value):
        self.argument_controller.update(lissajous_ny=float(value))

    @property
    def lissajous_phase(self):
        if self.argument_controller.get('lissajous_phase') == None:
            self.argument_controller.update(lissajous_phase=0)  # default
        return self.argument_controller.get('lissajous_phase')

    @lissajous_phase.setter
    def lissajous_phase(self, value):
        self.argument_controller.update(lissajous_phase=float(value))

    @property
    def kernel_mode(self):
        if self.argument_controller.get('kernel_mode') == None:
            self.argument_controller.update(kernel_mode=0)  # default
        return self.argument_controller.get('kernel_mode')

    @kernel_mode.setter
    def kernel_mode(self, value):
        self.argument_controller.update(kernel_mode=int(value))
        self.device.change_video_parameters(kernelMode=KERNEL_LIST[self.argument_controller.get('kernel_mode')],
                                      givenPixel=self.argument_controller.get('given_pixel'),
                                      acquisitionCutoff=self.argument_controller.get('acquisition_cutoff'),
                                      acquisitionWindow=self.argument_controller.get('acquisition_window'))

    @property
    def given_pixel(self):
        if self.argument_controller.get('given_pixel') == None:
            self.argument_controller.update(given_pixel=0)  # default
        return self.argument_controller.get('given_pixel')

    @given_pixel.setter
    def given_pixel(self, value):
        self.argument_controller.update(given_pixel=int(value))
        self.device.change_video_parameters(kernelMode=KERNEL_LIST[self.argument_controller.get('kernel_mode')],
                                      givenPixel=self.argument_controller.get('given_pixel'),
                                      acquisitionCutoff=self.argument_controller.get('acquisition_cutoff'),
                                      acquisitionWindow=self.argument_controller.get('acquisition_window'))

    @property
    def acquisition_cutoff(self):
        if self.argument_controller.get('acquisition_cutoff') == None:
            self.argument_controller.update(acquisition_cutoff=0)  # default
        return self.argument_controller.get('acquisition_cutoff')

    @acquisition_cutoff.setter
    def acquisition_cutoff(self, value):
        self.argument_controller.update(acquisition_cutoff=int(value))
        #variables = [self.argument_controller.get('kernel_mode'), self.argument_controller.get('given_pixel'),
        #             self.argument_controller.get('acquisition_cutoff'),
        #             self.argument_controller.get('acquisition_window')]
        #if not any(x is None for x in variables):
        self.device.change_video_parameters(kernelMode=KERNEL_LIST[self.argument_controller.get('kernel_mode')],
                                      givenPixel=self.argument_controller.get('given_pixel'),
                                      acquisitionCutoff=self.argument_controller.get('acquisition_cutoff'),
                                      acquisitionWindow=self.argument_controller.get('acquisition_window'))

    @property
    def acquisition_window(self):
        if self.argument_controller.get('acquisition_window') == None:
            self.argument_controller.update(acquisition_window=0)  # default
        return self.argument_controller.get('acquisition_window')

    @acquisition_window.setter
    def acquisition_window(self, value):
        self.argument_controller.update(acquisition_window=int(value))
        #variables = [self.argument_controller.get('kernel_mode'), self.argument_controller.get('given_pixel'),
        #             self.argument_controller.get('acquisition_cutoff'),
        #             self.argument_controller.get('acquisition_window')]
        #if not any(x is None for x in variables):
        self.device.change_video_parameters(kernelMode=KERNEL_LIST[self.argument_controller.get('kernel_mode')],
                                      givenPixel=self.argument_controller.get('given_pixel'),
                                      acquisitionCutoff=self.argument_controller.get('acquisition_cutoff'),
                                      acquisitionWindow=self.argument_controller.get('acquisition_window'))

    @property
    def magboard_switches(self):
        if self.argument_controller.get('magboard_switches') == None:
            self.argument_controller.update(magboard_switches='000000')  # default
        return self.argument_controller.get('magboard_switches')

    @magboard_switches.setter
    def magboard_switches(self, value):
        self.argument_controller.update(magboard_switches=str(value))
        self.device.change_magnification_switches(str(value))

    @property
    def offset_adc0(self):
        if self.argument_controller.get('offset_adc0') == None:
            self.argument_controller.update(offset_adc0=0)  # default
        return self.argument_controller.get('offset_adc0')

    @offset_adc0.setter
    def offset_adc0(self, value):
        self.argument_controller.update(offset_adc0=float(value))
        self.device.change_offset_adc('001', float(value), True)

    @property
    def offset_adc1(self):
        if self.argument_controller.get('offset_adc1') == None:
            self.argument_controller.update(offset_adc1=0)  # default
        return self.argument_controller.get('offset_adc1')

    @offset_adc1.setter
    def offset_adc1(self, value):
        self.argument_controller.update(offset_adc1=float(value))
        self.device.change_offset_adc('000', float(value), True)

    @property
    def offset_adc2(self):
        if self.argument_controller.get('offset_adc2') == None:
            self.argument_controller.update(offset_adc2=0)  # default
        return self.argument_controller.get('offset_adc2')

    @offset_adc2.setter
    def offset_adc2(self, value):
        self.argument_controller.update(offset_adc2=float(value))
        self.device.change_offset_adc('011', float(value), False)

    @property
    def offset_adc3(self):
        if self.argument_controller.get('offset_adc3') == None:
            self.argument_controller.update(offset_adc3=0)  # default
        return self.argument_controller.get('offset_adc3')

    @offset_adc3.setter
    def offset_adc3(self, value):
        self.argument_controller.update(offset_adc3=float(value))
        self.device.change_offset_adc('010', float(value), False)

    @property
    def multiblock0(self):
        if self.argument_controller.get('multiblock0') == None:
            self.argument_controller.update(multiblock0=0)  # default
        return self.argument_controller.get('multiblock0')

    @multiblock0.setter
    def multiblock0(self, value):
        self.argument_controller.update(multiblock0=float(value))
        variables = [self.argument_controller.get('multiblock0'), self.argument_controller.get('multiblock1'),
                     self.argument_controller.get('multiblock2'),
                     self.argument_controller.get('multiblock3')]
        if not any(x is None for x in variables):
            self.device.change_external_calibration(variables)
            self.device.change_external_values(65535)

    @property
    def multiblock1(self):
        if self.argument_controller.get('multiblock1') == None:
            self.argument_controller.update(multiblock1=0)  # default
        return self.argument_controller.get('multiblock1')

    @multiblock1.setter
    def multiblock1(self, value):
        self.argument_controller.update(multiblock1=float(value))
        variables = [self.argument_controller.get('multiblock0'), self.argument_controller.get('multiblock1'),
                     self.argument_controller.get('multiblock2'),
                     self.argument_controller.get('multiblock3')]
        if not any(x is None for x in variables):
            self.device.change_external_calibration(variables)
            self.device.change_external_values(65535)

    @property
    def multiblock2(self):
        if self.argument_controller.get('multiblock2') == None:
            self.argument_controller.update(multiblock2=0)  # default
        return self.argument_controller.get('multiblock2')

    @multiblock2.setter
    def multiblock2(self, value):
        self.argument_controller.update(multiblock2=float(value))
        variables = [self.argument_controller.get('multiblock0'), self.argument_controller.get('multiblock1'),
                     self.argument_controller.get('multiblock2'),
                     self.argument_controller.get('multiblock3')]
        if not any(x is None for x in variables):
            self.device.change_external_calibration(variables)
            self.device.change_external_values(65535)

    @property
    def multiblock3(self):
        if self.argument_controller.get('multiblock3') == None:
            self.argument_controller.update(multiblock3=0)  # default
        return self.argument_controller.get('multiblock3')

    @multiblock3.setter
    def multiblock3(self, value):
        self.argument_controller.update(multiblock3=float(value))
        variables = [self.argument_controller.get('multiblock0'), self.argument_controller.get('multiblock1'),
                     self.argument_controller.get('multiblock2'),
                     self.argument_controller.get('multiblock3')]
        if not any(x is None for x in variables):
            self.device.change_external_calibration(variables)
            self.device.change_external_values(65535)

    @property
    def mag_multiblock0(self):
        if self.argument_controller.get('mag_multiblock0') == None:
            self.argument_controller.update(mag_multiblock0=0)  # default
        return self.argument_controller.get('mag_multiblock0')

    @mag_multiblock0.setter
    def mag_multiblock0(self, value):
        self.argument_controller.update(mag_multiblock0=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)

    @property
    def mag_multiblock1(self):
        if self.argument_controller.get('mag_multiblock1') == None:
            self.argument_controller.update(mag_multiblock1=0)  # default
        return self.argument_controller.get('mag_multiblock1')

    @mag_multiblock1.setter
    def mag_multiblock1(self, value):
        self.argument_controller.update(mag_multiblock1=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)

    @property
    def mag_multiblock2(self):
        if self.argument_controller.get('mag_multiblock2') == None:
            self.argument_controller.update(mag_multiblock2=0)  # default
        return self.argument_controller.get('mag_multiblock2')

    @mag_multiblock2.setter
    def mag_multiblock2(self, value):
        self.argument_controller.update(mag_multiblock2=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)

    @property
    def mag_multiblock3(self):
        if self.argument_controller.get('mag_multiblock3') == None:
            self.argument_controller.update(mag_multiblock3=0)  # default
        return self.argument_controller.get('mag_multiblock3')

    @mag_multiblock3.setter
    def mag_multiblock3(self, value):
        self.argument_controller.update(mag_multiblock3=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)

    @property
    def mag_multiblock4(self):
        if self.argument_controller.get('mag_multiblock4') == None:
            self.argument_controller.update(mag_multiblock4=0)  # default
        return self.argument_controller.get('mag_multiblock4')

    @mag_multiblock4.setter
    def mag_multiblock4(self, value):
        self.argument_controller.update(mag_multiblock4=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)

    @property
    def mag_multiblock5(self):
        if self.argument_controller.get('mag_multiblock5') == None:
            self.argument_controller.update(mag_multiblock5=0)  # default
        return self.argument_controller.get('mag_multiblock5')

    @mag_multiblock5.setter
    def mag_multiblock5(self, value):
        self.argument_controller.update(mag_multiblock5=float(value))
        variables = [self.argument_controller.get('mag_multiblock0'), self.argument_controller.get('mag_multiblock1'),
                     self.argument_controller.get('mag_multiblock2'), self.argument_controller.get('mag_multiblock3'),
                     self.argument_controller.get('mag_multiblock4'), self.argument_controller.get('mag_multiblock5')]
        if not any(x is None for x in variables):
            self.device.change_magnification_calibration(variables)


    @property
    def input1_mux(self):
        if self.argument_controller.get('input1_mux') == None:
            self.argument_controller.update(input1_mux=0)  # default
        return self.argument_controller.get('input1_mux')

    @input1_mux.setter
    def input1_mux(self, value):
        self.argument_controller.update(input1_mux=int(value))
        self.device.set_input_mux(0, int(value))
        self.property_changed_event.fire("input1_mux")

    @property
    def input2_mux(self):
        if self.argument_controller.get('input2_mux') == None:
            self.argument_controller.update(input2_mux=0)  # default
        return self.argument_controller.get('input2_mux')

    @input2_mux.setter
    def input2_mux(self, value):
        self.argument_controller.update(input2_mux=int(value))
        self.device.set_input_mux(1, int(value))
        self.property_changed_event.fire("input2_mux")

    @property
    def routex_mux(self):
        if self.argument_controller.get('routex_mux') == None:
            self.argument_controller.update(routex_mux=0)  # default
        return self.argument_controller.get('routex_mux')

    @routex_mux.setter
    def routex_mux(self, value):
        self.argument_controller.update(routex_mux=int(value))
        variables = [0, self.argument_controller.get('routex_mux'), self.argument_controller.get('routex_mux_intensity'),
                     self.argument_controller.get('routex_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routex_mux")

    @property
    def routex_mux_intensity(self):
        if self.argument_controller.get('routex_mux_intensity') == None:
            self.argument_controller.update(routex_mux_intensity=0)  # default
        return self.argument_controller.get('routex_mux_intensity')

    @routex_mux_intensity.setter
    def routex_mux_intensity(self, value):
        self.argument_controller.update(routex_mux_intensity=int(value))
        variables = [0, self.argument_controller.get('routex_mux'),
                     self.argument_controller.get('routex_mux_intensity'),
                     self.argument_controller.get('routex_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routex_mux_intensity")

    @property
    def routex_mux_averages(self):
        if self.argument_controller.get('routex_mux_averages') == None:
            self.argument_controller.update(routex_mux_averages=0)  # default
        return self.argument_controller.get('routex_mux_averages')

    @routex_mux_averages.setter
    def routex_mux_averages(self, value):
        self.argument_controller.update(routex_mux_averages=int(value))
        variables = [0, self.argument_controller.get('routex_mux'),
                     self.argument_controller.get('routex_mux_intensity'),
                     self.argument_controller.get('routex_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routex_mux_averages")

    @property
    def routey_mux(self):
        if self.argument_controller.get('routey_mux') == None:
            self.argument_controller.update(routey_mux=0)  # default
        return self.argument_controller.get('routey_mux')

    @routey_mux.setter
    def routey_mux(self, value):
        self.argument_controller.update(routey_mux=int(value))
        variables = [1, self.argument_controller.get('routey_mux'),
                     self.argument_controller.get('routey_mux_intensity'),
                     self.argument_controller.get('routey_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routey_mux")

    @property
    def routey_mux_intensity(self):
        if self.argument_controller.get('routey_mux_intensity') == None:
            self.argument_controller.update(routey_mux_intensity=0)  # default
        return self.argument_controller.get('routey_mux_intensity')

    @routey_mux_intensity.setter
    def routey_mux_intensity(self, value):
        self.argument_controller.update(routey_mux_intensity=int(value))
        variables = [1, self.argument_controller.get('routey_mux'),
                     self.argument_controller.get('routey_mux_intensity'),
                     self.argument_controller.get('routey_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routey_mux_intensity")

    @property
    def routey_mux_averages(self):
        if self.argument_controller.get('routey_mux_averages') == None:
            self.argument_controller.update(routey_mux_averages=0)  # default
        return self.argument_controller.get('routey_mux_averages')

    @routey_mux_averages.setter
    def routey_mux_averages(self, value):
        self.argument_controller.update(routey_mux_averages=int(value))
        variables = [1, self.argument_controller.get('routey_mux'),
                     self.argument_controller.get('routey_mux_intensity'),
                     self.argument_controller.get('routey_mux_averages')]
        if not any(x is None for x in variables):
            self.device.set_route_mux(*variables)
        self.property_changed_event.fire("routey_mux_averages")
    @property
    def mux_output_type(self):
        if self.argument_controller.get('mux_output_type') == None:
            self.argument_controller.update(mux_output_type=[0] * 8)  # default
        return self.argument_controller.get('mux_output_type')

    @mux_output_type.setter
    def mux_output_type(self, value: list):
        self.argument_controller.update(mux_output_type=value)
        self.output1_mux_type = value[0]
        self.output2_mux_type = value[1]
        self.output3_mux_type = value[2]
        self.output4_mux_type = value[3]
        self.output5_mux_type = value[4]

    @property
    def mux_output_freq(self):
        if self.argument_controller.get('mux_output_freq') == None:
            self.argument_controller.update(mux_output_freq=[0] * 8)  # default
        return self.argument_controller.get('mux_output_freq')

    @mux_output_freq.setter
    def mux_output_freq(self, value: list):
        self.argument_controller.update(mux_output_freq=value)
        self.output1_mux_freq = value[0]
        self.output2_mux_freq = value[1]
        self.output3_mux_freq = value[2]
        self.output4_mux_freq = value[3]
        self.output5_mux_freq = value[4]

    @property
    def mux_output_input(self):
        if self.argument_controller.get('mux_output_input') == None:
            self.argument_controller.update(mux_output_input=[0] * 8)  # default
        return self.argument_controller.get('mux_output_input')

    @mux_output_input.setter
    def mux_output_input(self, value: list):
        self.argument_controller.update(mux_output_input=value)
        self.output1_mux_input = value[0]
        self.output2_mux_input = value[1]
        self.output3_mux_input = value[2]
        self.output4_mux_input = value[3]
        self.output5_mux_input = value[4]

    @property
    def mux_output_input_div(self):
        if self.argument_controller.get('mux_output_input_div') == None:
            self.argument_controller.update(mux_output_input_div=[0] * 8)  # default
        return self.argument_controller.get('mux_output_input_div')

    @mux_output_input_div.setter
    def mux_output_input_div(self, value: list):
        self.argument_controller.update(mux_output_input_div=value)
        self.output1_mux_input_div = value[0]
        self.output2_mux_input_div = value[1]
        self.output3_mux_input_div = value[2]
        self.output4_mux_input_div = value[3]
        self.output5_mux_input_div = value[4]

    @property
    def mux_output_delay(self):
        if self.argument_controller.get('mux_output_delay') == None:
            self.argument_controller.update(mux_output_delay=[0] * 8)  # default
        return self.argument_controller.get('mux_output_delay')

    @mux_output_delay.setter
    def mux_output_delay(self, value: list):
        self.argument_controller.update(mux_output_delay=value)
        self.output1_mux_delay = value[0]
        self.output2_mux_delay = value[1]
        self.output3_mux_delay = value[2]
        self.output4_mux_delay = value[3]
        self.output5_mux_delay = value[4]


    """
    Creating the functions for the output multiplexer. I have used the property function for efficiency
    """
    def get_output1_mux_type(channel: int):
        def wrapper(self):
            if self.argument_controller.get('mux_output_type') == None:
                self.argument_controller.update(mux_output_type=[0] * 8)  # default
            return self.argument_controller.get('mux_output_type')[channel]
        return wrapper

    def set_output_mux_type(channel: int):
        def wrapper(self, value):
            temp_list = self.argument_controller.get('mux_output_type', [0] * 8)
            temp_list[channel] = int(value)
            self.argument_controller.update(mux_output_type=temp_list)
            variables = [channel, self.argument_controller.get('mux_output_type', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_freq', [0] * 8)[channel],
                         self.argument_controller.get('mu"x_output_input', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input_div', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_delay', [0] * 8)[channel]]
            self.device.set_output_mux(*variables)
        return wrapper

    def get_output_mux_freq(channel):
        def wrapper(self):
            if self.argument_controller.get('mux_output_freq') == None:
                self.argument_controller.update(mux_output_freq=[0] * 8)  # default
            return self.argument_controller.get('mux_output_freq')[channel]
        return wrapper

    def set_output_mux_freq(channel):
        def wrapper(self, value):
            temp_list = self.argument_controller.get('mux_output_freq',  [0] * 8)
            temp_list[channel] = int(value)
            self.argument_controller.update(mux_output_freq=temp_list)
            variables = [channel, self.argument_controller.get('mux_output_type', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_freq', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input_div', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_delay', [0] * 8)[channel]]
            self.device.set_output_mux(*variables)
        return wrapper

    def get_output_mux_delay(channel):
        def wrapper(self):
            if self.argument_controller.get('mux_output_delay') == None:
                self.argument_controller.update(mux_output_delay=[0] * 8)  # default
            return self.argument_controller.get('mux_output_delay')[channel]
        return wrapper

    def set_output_mux_delay(channel):
        def wrapper(self, value):
            temp_list = self.argument_controller.get('mux_output_delay', [0] * 8)
            temp_list[channel] = int(value)
            self.argument_controller.update(mux_output_delay=temp_list)
            variables = [channel, self.argument_controller.get('mux_output_type', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_freq', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input_div', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_delay', [0] * 8)[channel]]
            self.device.set_output_mux(*variables)
        return wrapper

    def get_output_mux_input(channel):
        def wrapper(self):
            if self.argument_controller.get('mux_output_input') == None:
                self.argument_controller.update(mux_output_input=[0] * 8)  # default
            return self.argument_controller.get('mux_output_input')[channel]
        return wrapper

    def set_output_mux_input(channel):
        def wrapper(self, value):
            temp_list = self.argument_controller.get('mux_output_input', [0] * 8)
            temp_list[channel] = int(value)
            self.argument_controller.update(mux_output_input=temp_list)
            variables = [channel, self.argument_controller.get('mux_output_type', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_freq', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input_div', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_delay', [0] * 8)[channel]]
            self.device.set_output_mux(*variables)
        return wrapper

    def get_output_mux_input_div(channel):
        def wrapper(self):
            if self.argument_controller.get('mux_output_input_div') == None:
                self.argument_controller.update(mux_output_input_div=[0] * 8)  # default
            return self.argument_controller.get('mux_output_input_div')[channel]
        return wrapper

    def set_output_mux_input_div(channel):
        def wrapper(self, value):
            temp_list = self.argument_controller.get('mux_output_input_div', [0] * 8)
            temp_list[channel] = int(value)
            self.argument_controller.update(mux_output_input_div=temp_list)
            variables = [channel, self.argument_controller.get('mux_output_type', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_freq', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_input_div', [0] * 8)[channel],
                         self.argument_controller.get('mux_output_delay', [0] * 8)[channel]]
            self.device.set_output_mux(*variables)
        return wrapper

    output1_mux_type = property(get_output1_mux_type(0), set_output_mux_type(0))
    output1_mux_freq = property(get_output_mux_freq(0), set_output_mux_freq(0))
    output1_mux_input = property(get_output_mux_input(0), set_output_mux_input(0))
    output1_mux_input_div = property(get_output_mux_input_div(0), set_output_mux_input_div(0))
    output1_mux_delay = property(get_output_mux_delay(0), set_output_mux_delay(0))

    output2_mux_type = property(get_output1_mux_type(1), set_output_mux_type(1))
    output2_mux_freq = property(get_output_mux_freq(1), set_output_mux_freq(1))
    output2_mux_input = property(get_output_mux_input(1), set_output_mux_input(1))
    output2_mux_input_div = property(get_output_mux_input_div(1), set_output_mux_input_div(1))
    output2_mux_delay = property(get_output_mux_delay(1), set_output_mux_delay(1))

    output3_mux_type = property(get_output1_mux_type(2), set_output_mux_type(2))
    output3_mux_freq = property(get_output_mux_freq(2), set_output_mux_freq(2))
    output3_mux_input = property(get_output_mux_input(2), set_output_mux_input(2))
    output3_mux_input_div = property(get_output_mux_input_div(2), set_output_mux_input_div(2))
    output3_mux_delay = property(get_output_mux_delay(2), set_output_mux_delay(2))

    output4_mux_type = property(get_output1_mux_type(3), set_output_mux_type(3))
    output4_mux_freq = property(get_output_mux_freq(3), set_output_mux_freq(3))
    output4_mux_input = property(get_output_mux_input(3), set_output_mux_input(3))
    output4_mux_input_div = property(get_output_mux_input_div(3), set_output_mux_input_div(3))
    output4_mux_delay = property(get_output_mux_delay(3), set_output_mux_delay(3))

    output5_mux_type = property(get_output1_mux_type(4), set_output_mux_type(4))
    output5_mux_freq = property(get_output_mux_freq(4), set_output_mux_freq(4))
    output5_mux_input = property(get_output_mux_input(4), set_output_mux_input(4))
    output5_mux_input_div = property(get_output_mux_input_div(4), set_output_mux_input_div(4))
    output5_mux_delay = property(get_output_mux_delay(4), set_output_mux_delay(4))




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


class Device(scan_base.ScanDevice):
    def __init__(self, instrument):
        self.scan_device_id = "open_scan_device"
        self.scan_device_is_secondary = True
        self.scan_device_name = _("OpScan")
        self.__channels = self.__get_channels()
        self.__frame = None
        self.__frame_number = 0
        self.__instrument = instrument
        self.__sizez = 2
        self.__probe_position = [0, 0]
        self.__probe_position_pixels = [0, 0]
        self.__rotation = 0.
        self.__is_scanning = False
        self.on_device_state_changed = None
        self.flyback_pixels = 0
        self.__buffer = list()
        self.__sequence_buffer_size = 0
        self.__view_buffer_size = 20
        self.bottom_blanker = 0
        self.scan_engine = ScanEngine()

        self.has_data_event = threading.Event()

    def close(self):
        pass

    def stop(self) -> None:
        """Stop acquiring."""
        if self.__is_scanning:
            self.__is_scanning = False

    def set_idle_position_by_percentage(self, x: float, y: float) -> None:
        """Set the idle position as a percentage of the last used frame parameters."""
        pass

    def cancel(self) -> None:
        """Cancel acquisition (immediate)."""
        if self.__is_scanning:
            self.__is_scanning = False

    def __get_channels(self) -> typing.List[Channel]:
        channels = [Channel(0, "ListScan", False), Channel(1, "BF", False), Channel(2, "ADF", True)]
        return channels

    def __get_initial_profiles(self) -> typing.List[scan_base.ScanFrameParameters]:
        profiles = list()
        profiles.append(scan_base.ScanFrameParameters(
            {"size": (128, 128), "pixel_time_us": 0.5, "fov_nm": 4000., "rotation_rad": 0.393}))
        profiles.append(scan_base.ScanFrameParameters({"size": (128, 128), "pixel_time_us": 1, "fov_nm": 100.}))
        profiles.append(scan_base.ScanFrameParameters({"size": (512, 512), "pixel_time_us": 1, "fov_nm": 100.}))
        return profiles

    def get_channel_name(self, channel_index: int) -> str:
        return self.__channels[channel_index].name

    def set_frame_parameters(self, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Called just before and during acquisition.
        Device should use these parameters for new acquisition; and update to these parameters during acquisition.
        """
        self.__frame_parameters = copy.deepcopy(frame_parameters)
        self.scan_engine.set_frame_parameters(frame_parameters)

    def save_frame_parameters(self) -> None:
        """Called when shutting down. Save frame parameters to persistent storage."""
        pass

    def get_current_image_size(self, frame_parameters: scan_base.ScanFrameParameters) -> tuple:
        value = frame_parameters.get_parameter("subscan_pixel_size", None)
        if value == None:
            value = frame_parameters.as_dict()["pixel_size"]
        return value


    def start_frame(self, is_continuous: bool) -> int:
        """Start acquiring. Return the frame number."""
        if not self.__is_scanning:
            self.__buffer = list()
            self.__start_next_frame()
            self.__is_scanning = True
        return self.__frame_number

    def __start_next_frame(self):
        frame_parameters = copy.deepcopy(self.__frame_parameters)
        self.__scan_context = stem_controller.ScanContext()
        channels = [copy.deepcopy(channel) for channel in self.__channels if channel.enabled]  # channel enabled is here
        size = Geometry.IntSize.make(
            frame_parameters.subscan_pixel_size if frame_parameters.subscan_pixel_size else frame_parameters.size)
        for channel in channels:
            channel.data = numpy.zeros(tuple(size), numpy.float32)
        is_synchronized_scan = frame_parameters.get_parameter("external_clock_mode", 0) != 0
        self.__frame_number = self.scan_engine.device.get_frame_counter()
        self.__start_frame = self.__frame_number
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

        if self.__frame is None:
            self.__start_next_frame()

        current_frame = self.__frame  # this is from Frame Class defined above
        assert current_frame is not None
        #frame_number = current_frame.frame_number
        self.__frame_number = self.scan_engine.device.get_frame_counter()
        is_synchronized_scan = current_frame.frame_parameters.get_parameter("external_clock_mode", 0) != 0
        if is_synchronized_scan:
            current_frame.complete = self.scan_engine.device.get_dma_status_idle()[0] == 2
            if current_frame.complete:
                sub_area = ((0, 0), self.get_current_image_size(current_frame.frame_parameters))
            else:
                (x, y) = self.get_current_image_size(current_frame.frame_parameters)
                lines = self.scan_engine.device.get_pixel_counter() // y
                sub_area = ((0, 0), (lines, y))
        else:
            current_frame.complete = self.__frame_number != self.__start_frame
            sub_area = ((0, 0), self.get_current_image_size(current_frame.frame_parameters))

        if DEBUG:
            print(f"{current_frame.complete} and {self.scan_engine.device.get_pixel_counter()} and {self.__frame_number} and {self.__start_frame} "
              f"and {self.scan_engine.device.get_dma_status_idle()} and {self.scan_engine.device.get_bd_status_cmplt()} "
              f"and {self.get_current_image_size(current_frame.frame_parameters)}")

        data_elements = list()

        for channel in current_frame.channels:
            data_element = dict()
            data_array = self.scan_engine.receive_total_frame(channel.channel_id)
            data_element["data"] = data_array
            properties = current_frame.frame_parameters.as_dict()
            properties["center_x_nm"] = current_frame.frame_parameters.center_nm[1]
            properties["center_y_nm"] = current_frame.frame_parameters.center_nm[0]
            properties["rotation_deg"] = math.degrees(current_frame.frame_parameters.rotation_rad)
            properties["channel_id"] = channel.channel_id
            data_element["properties"] = properties
            if data_array is not None:
                data_elements.append(data_element)

        if current_frame.complete:
            if len(self.__buffer) > 0 and len(self.__buffer[-1]) != len(data_elements):
                self.__buffer = list()
            self.__buffer.append(data_elements)
            while len(self.__buffer) > self.__sequence_buffer_size + self.__view_buffer_size:
                del self.__buffer[self.__sequence_buffer_size]
            self.__frame = None

        # return data_elements, complete, bad_frame, sub_area, frame_number, pixels_to_skip
        return data_elements, current_frame.complete, False, sub_area, self.__frame_number, 0

    # This one is called in scan_base
    def prepare_synchronized_scan(self, scan_frame_parameters: scan_base.ScanFrameParameters, *, camera_exposure_ms,
                                  **kwargs) -> None:
        #scan_frame_parameters.set_parameter("pixel_time_us", int(1000 * camera_exposure_ms))
        scan_frame_parameters.set_parameter("external_clock_mode", 1)

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

    @property
    def pixel_time(self):
        return self.__pixeltime

    @pixel_time.setter
    def pixel_time(self, value):
        self.__pixeltime = value / 1e6

    @property
    def scan_rotation(self):
        return self.__rotation

    @scan_rotation.setter
    def scan_rotation(self, value):
        self.__rotation = value * 180 / numpy.pi

    @property
    def Image_area(self):
        return self.__scan_area

    @Image_area.setter
    def Image_area(self, value):
        self.__scan_area = value

    @property
    def probe_pos(self):
        return self.__probe_position

    @probe_pos.setter
    def probe_pos(self, value):
        self.__probe_position = value
        self.scan_engine.set_probe_position(value.x, value.y)
        # This is a very strange behavior of geometry class. Very misleading. Value is a tuple like
        # (x=0.1, y=0.3) but value[0] gives y value while value[1] gives x value. You can check here
        # print(f'value is {value} and first is {value[0]}. Second is {value[1]}')
        # If you using this func, please call it with (y, x)
        #px, py = round(self.__probe_position[1] * self.__scan_area[1]), round(
        #    self.__probe_position[0] * self.__scan_area[0])
        #self.__probe_position_pixels = [px, py]

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

    def show_configuration_dialog(self, api_broker) -> None:
        """Open settings dialog, if any."""
        #api = api_broker.get_api(version="1", ui_version="1")
        #document_controller = api.application.document_controllers[0]._document_controller
        #myConfig = ConfigDialog(document_controller)


# def run(instrument: ivg_inst.ivgInstrument):
#    scan_device = Device(instrument)
#    component_types = {"scan_device"}  # the set of component types that this component represents
#    Registry.register_component(scan_device, component_types)

class ScanSettings(scan_base.ScanSettings):

    def __init__(self, scan_modes, frame_parameters_factory, current_settings_index = 0, record_settings_index = 0, open_configuration_dialog_fn = None) -> None:
        super(ScanSettings, self).__init__(scan_modes, frame_parameters_factory, current_settings_index, record_settings_index, open_configuration_dialog_fn)

    def open_configuration_interface(self, api_broker: typing.Any) -> None:
        if callable(self.__open_configuration_dialog_fn):
            self.__open_configuration_dialog_fn(api_broker)


class ScanModule(scan_base.ScanModule):
    def __init__(self, instrument) -> None:
        self.stem_controller_id = instrument.instrument_id
        self.device = Device(instrument)
        setattr(self.device, "priority", 20)
        scan_modes = (
            scan_base.ScanSettingsMode(_("Fast"), "fast",
                                       scan_base.ScanFrameParameters(pixel_size=(128, 128), pixel_time_us=1,
                                                                     fov_nm=4000)),
            scan_base.ScanSettingsMode(_("Slow"), "slow",
                                       scan_base.ScanFrameParameters(pixel_size=(512, 512), pixel_time_us=1,
                                                                     fov_nm=4000)),
            scan_base.ScanSettingsMode(_("Record"), "record",
                                       scan_base.ScanFrameParameters(pixel_size=(1024, 1024), pixel_time_us=1,
                                                                     fov_nm=4000))
        )
        self.settings = ScanSettings(scan_modes, lambda d: scan_base.ScanFrameParameters(d), 0, 2,
                                     open_configuration_dialog_fn=show_configuration_dialog)



def show_configuration_dialog(api_broker) -> None:
    """Open settings dialog, if any."""
    api = api_broker.get_api(version="1", ui_version="1")
    document_controller = api.application.document_controllers[0]._document_controller
    myConfig = ConfigDialog(document_controller)


def run(instrument) -> None:
    Registry.register_component(ScanModule(instrument), {"scan_module"})


def stop() -> None:
    Registry.unregister_component(Registry.get_component("scan_module"), {"scan_module"})