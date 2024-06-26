# standard libraries
import threading, numpy, queue, logging

from nion.utils import Event
from nion.utils import Observable
from nion.instrumentation import HardwareSource
try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data


class OptSpecDevice(Observable.Observable):
    def __init__(self, MANUFACTURER):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.send_gratings = Event.Event()
        self.warn_panel = Event.Event()
        self.send_data = Event.Event()
        self.warn_panel_over = Event.Event()

        self.__queue = queue.Queue()
        self.__running = False
        self.__successful = False
        self.__model = MANUFACTURER
        self.__thread = None
        self.__instrument = None

    def init(self):
        if self.__model == 'DEBUG':
            from . import spec_vi as optSpec
        elif self.__model == 'ATTOLIGHT':
            from . import spec_attolight as optSpec
        elif self.__model == 'PRINCETON':
            from . import spec as optSpec

        self.__sendmessage = optSpec.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        if self.__model == 'PRINCETON':
            set_file = read_data.FileManager('global_settings')
            SERIAL_PORT_PRINCETON = set_file.settings["spectrometer"]["COM_PRINCETON"]
            self.__Spec = optSpec.OptSpectrometer(self.__sendmessage, SERIAL_PORT_PRINCETON)
        else:
            self.__Spec = optSpec.OptSpectrometer(self.__sendmessage)

        if not self.__Spec.success:
            return False

        self.__cameraSize = 25.6
        self.__gratings = self.__Spec.gratingNames()
        self.send_gratings.fire(self.__gratings)
        self.__lpmms = self.__Spec.gratingLPMM()
        self.__fl = self.__Spec.get_specFL()
        self.__cameraPixels = self.__Spec.camera_pixels()
        self.__cameraName = self.__Spec.which_camera()
        self.__devAngle = self.__Spec.deviation_angle()

        self.__calibration_controls = {
            "x_scale_control": "Princeton_CL_nmperpixel",
            "x_offset_control": "Princeton_CL_nmOffset",
            "x_units_value": "nm",
            "y_scale_control": "Princeton_CL_radsperpixel",
            "y_units_value": "rad",
            "intensity_units_value": "Counts",
            "counts_per_electron_control": "Princeton_CL_CountsPerElectron"
        }

        #Checking if AUTOSTEM exists or not
        AUTOSTEM_CONTROLLER_ID = "autostem_controller"
        autostem = HardwareSource.HardwareSourceManager().get_instrument_by_id(AUTOSTEM_CONTROLLER_ID)
        if autostem == None:
            self.__instrument = HardwareSource.HardwareSourceManager().get_instrument_by_id('orsay_controller')
        else:
            tuning_manager = autostem.tuning_manager
            self.__instrument = tuning_manager.instrument_controller

        self.__eirecamera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__cameraName)

        try:
            self.__eirecamera.camera.calibration_controls = self.__calibration_controls
        except AttributeError:
            logging.info("***OPT SPEC***: Can't set calibration controls.")

        return (True and self.__eirecamera is not None)

    def upt(self):
        self.property_changed_event.fire('wav_f')
        self.property_changed_event.fire('grating_f')
        self.property_changed_event.fire('entrance_slit_f')
        self.property_changed_event.fire('exit_slit_f')
        self.property_changed_event.fire('which_slit_f')
        self.property_changed_event.fire('lpmm_f')
        self.property_changed_event.fire('dispersion_nmmm_f')
        self.property_changed_event.fire('pixel_size_f')
        self.property_changed_event.fire('dispersion_pixels_f')
        self.property_changed_event.fire('fov_f')
        self.property_changed_event.fire('camera_size_f')
        self.property_changed_event.fire('camera_pixels_f')
        self.property_changed_event.fire('focalLength_f')
        self.upt_calibs()
        if not self.__successful: self.__successful = True

    """
    def upt_values(self):
        self.property_changed_event.fire('wav_f')
        self.property_changed_event.fire('lpmm_f')
        self.property_changed_event.fire('dispersion_nmmm_f')
        self.property_changed_event.fire('pixel_size_f')
        self.property_changed_event.fire('dispersion_pixels_f')
        self.property_changed_event.fire('fov_f')
        self.property_changed_event.fire('camera_size_f')
        self.property_changed_event.fire('camera_pixels_f')
        self.property_changed_event.fire('focalLength_f')
        self.upt_calibs()
    """

    def upt_calibs(self):
        read_data.InstrumentDictSetter("OptSpec", "Princeton_CL_nmperpixel", self.dispersion_f * self.__cameraSize / self.__cameraPixels)
        read_data.InstrumentDictSetter("OptSpec", "Princeton_CL_nmOffset", self.__wl - self.dispersion_f * self.__cameraSize / 2.)


    def measure(self):
        self.__running = True
        self.busy_event.fire('')
        self.warn_panel.fire()
        self.__thread = threading.Thread(target=self.measureThread)
        self.__thread.start()

    def measureThread(self):
        index = 0
        while self.__running:
            cam_data = self.__eirecamera.grab_next_to_finish()[0]
            cam_hor = numpy.sum(cam_data.data, axis=0) if len(cam_data.data.shape) > 1 else cam_data.data
            cam_total = numpy.sum(cam_hor)
            self.send_data.fire(cam_total, index)
            index += 1
            if index == 200: index = 0

    def abort(self):
        try:
            if self.__running:
                self.__running = False
                self.__thread.join()
                self.warn_panel_over.fire()
        except AttributeError:
            #No measure was happening
            pass
        self.property_changed_event.fire('')

    def sendMessageFactory(self):
        def sendMessage(message):
            try:
                if message:
                    self.__running = False
                    self.upt()
                    self.property_changed_event.fire('wav_f')
                    if self.__successful: self.upt_calibs()
            except:
                logging.info('***OPT SPECT***: Callback function issue.')

        return sendMessage

    @property
    def wav_f(self):
        try:
            self.__wl = self.__Spec.get_wavelength()
            return format(self.__wl, '.3f')
        except:
            return 'None'

    @wav_f.setter
    def wav_f(self, value):
        if self.__wl != float(value) and 0 <= float(value) <= 2500:
            self.__wl = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_wavelength, args=(self.__wl,)).start()
            self.__running = True

    @property
    def grating_f(self):
        try:
            self.__grating = self.__Spec.get_grating()
            return self.__grating
        except:
            return 0

    @grating_f.setter
    def grating_f(self, value):
        if self.__grating != value:
            self.__grating = value
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_grating, args=(self.__grating,)).start()
            self.__running = True

    @property
    def lpmm_f(self):
        try:
            return self.__lpmms[self.__grating]
        except:
            return 'None'

    @property
    def inc_angle_f(self):
        try:
            return self.dif_angle_f - self.__devAngle
        except:
            return 'None'

    @property
    def dif_angle_f(self):
        '''
        This is somewhat complicated. devAngle is a spectrometer property and are simple a
        contraint between two slits (central and camera center) and two angles. Incidence
        minus diffraction angle is always constant in a given spectrometer. Please see equation
        2.4 in diffraction grating handbook by Christopher Palmer. abs2 is the incidence plus
        the diffracted angle divided by two.
        '''
        try:
            ab2 = numpy.arcsin((1 / 2. * 1e-6 * self.__wl * self.lpmm_f) / numpy.cos(self.__devAngle / 2.))
            return (2 * ab2 + self.__devAngle) / 2.
        except:
            return 'None'

    @property
    def dispersion_f(self):
        '''
        Also confusing but just derivate diffraction equation. Note that alpha depends on wavelength
        but its derivative is zero because input is fixed. We wanna see difracted beam angle dispersion
        and not entrance. See diffraction grating handbook by Christopher Palmer.
        This is often called reciprocal linear dispersion. It is measured in nm/mm.
        '''
        try:
            return 1e6 / self.__lpmms[self.__grating] * numpy.cos(self.dif_angle_f) / self.__fl
        except:
            return 'None'

    @property
    def entrance_slit_f(self):
        try:
            self.__entrance_slit = self.__Spec.get_entrance()
            return self.__entrance_slit
        except:
            return 'None'

    @entrance_slit_f.setter
    def entrance_slit_f(self, value):
        if self.__entrance_slit != float(value) and 0 <= float(value) <= 5000:
            self.__entrance_slit = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_entrance,
                                                    args=(self.__entrance_slit,)).start()
            self.__running = True

    @property
    def exit_slit_f(self):
        try:
            self.__exit_slit = self.__Spec.get_exit()
            return self.__exit_slit
        except:
            return 'None'

    @exit_slit_f.setter
    def exit_slit_f(self, value):
        if self.__exit_slit != float(value) and 0 <= float(value) <= 5000:
            self.__exit_slit = float(value)
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_exit, args=(self.__exit_slit,)).start()
            self.__running = True

    @property
    def which_slit_f(self):
        try:
            self.__slit_choice = self.__Spec.get_which()
            return self.__slit_choice
        except:
            return -1

    @which_slit_f.setter
    def which_slit_f(self, value):
        if self.__slit_choice != value:
            self.__slit_choice = value
            self.busy_event.fire("")
            if not self.__running: threading.Thread(target=self.__Spec.set_which, args=(self.__slit_choice,)).start()
            self.__running = True

    @property
    def camera_size_f(self):
        try:
            return format(self.__cameraSize, '.1f')
        except:
            return 'None'

    @camera_size_f.setter
    def camera_size_f(self, value):
        self.__cameraSize = float(value)
        self.upt()

    @property
    def camera_pixels_f(self):
        try:
            return format(self.__cameraPixels, '.0f')
        except:
            return 'None'

    @camera_pixels_f.setter
    def camera_pixels_f(self, value):
        self.__cameraPixels = int(value)
        self.upt()

    @property
    def focalLength_f(self):
        try:
            return format(self.__fl, '.0f')
        except:
            return 'None'

    @focalLength_f.setter
    def focalLength_f(self, value):
        self.__fl = int(value)
        self.upt()

    @property
    def pixel_size_f(self):
        try:
            return self.__cameraSize / self.__cameraPixels * 1e3
        except:
            return 'None'

    @property
    def dispersion_nmmm_f(self):
        try:
            return format(self.dispersion_f, '.3f')
        except:
            return 'None'

    @property
    def dispersion_pixels_f(self):
        try:
            return format(self.dispersion_f * self.__cameraSize / self.__cameraPixels, '.3f')
        except:
            return 'None'

    @property
    def fov_f(self):
        try:
            return format(self.dispersion_f * self.__cameraSize, '.3f')
        except:
            return 'None'