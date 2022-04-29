# standard libraries
import threading
import logging
import smtplib
import time
import numpy

from nion.utils import Event
from nion.swift.model import HardwareSource
from nion.instrumentation import stem_controller
from nion.utils import Geometry

from ..aux_files.config import read_data

sender_email = "vg.lumiere@gmail.com"
receiver_email = "yvesauad@gmail.com"

message = """\
Subject: Objective Lens @ VG Lumiere

This message was automatically sent and means objective lens @ VG Lum. was shutdown because of its high temperature"""



set_file = read_data.FileManager('global_settings')

SERIAL_PORT_GUN = set_file.settings["IVG"]["COM_GUN"]
SERIAL_PORT_AIRLOCK = set_file.settings["IVG"]["COM_AIRLOCK"]
SENDMAIL = set_file.settings["IVG"]["SENDMAIL"]
TIME_FAST_PERIODIC = set_file.settings["IVG"]["FAST_PERIODIC"]["PERIOD"]
SLOW_PERIODIC = set_file.settings["IVG"]["SLOW_PERIODIC"]["ACTIVE"]
TIME_SLOW_PERIODIC = set_file.settings["IVG"]["SLOW_PERIODIC"]["PERIOD"]
OBJECTIVE_MAX_TEMPERATURE = set_file.settings["IVG"]["OBJECTIVE"]["MAX_TEMP"]
OBJECTIVE_RESISTANCE = set_file.settings["IVG"]["OBJECTIVE"]["RESISTANCE"]
TEMP_COEF = set_file.settings["IVG"]["OBJECTIVE"]["TEMP_COEF"]
MAX_PTS = set_file.settings["IVG"]["MAX_PTS"]

from . import gun as gun
from . import airlock as al

class ivgInstrument(stem_controller.STEMController):
    def __init__(self, instrument_id: str):
        super().__init__()
        self.priority = 20
        self.instrument_id = instrument_id
        self.property_changed_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.append_data = Event.Event()
        self.stage_event = Event.Event()

        self.cam_spim_over = Event.Event()
        self.spim_over = Event.Event()

        self.__set_file = read_data.FileManager('global_settings')

        self.__blanked = False
        self.__scan_context = stem_controller.ScanContext()
        self.__probe_position = None
        self.__live_probe_position = None
        self.__fov = 4.0 #Begin fov as 4.0 microns
        self.__is_subscan = [False, 1, 1]
        self.__spim_time = 0.
        self.__obj_stig = [0, 0]
        self.__gun_stig = [0, 0]
        self.__haadf_gain = 250
        self.__bf_gain = 250

        self.__EHT = self.__set_file.settings["global_settings"]["last_HT"]
        self.__obj_res_ref = OBJECTIVE_RESISTANCE
        self.__amb_temp = 23
        self.__stand = False
        self.__stage_moving = [False, False] #x and y stage moving
        self.__stage_thread = threading.Thread(target=self.stage_periodic_start, args=(),)

        self.__objWarning = False
        self.__obj_temp = self.__amb_temp
        self.__obj_res = self.__obj_res_ref
        self.__c1_vol = self.__c1_res = self.__c2_vol = self.__c2_res = 0.0


        self.__x_real_pos = self.__y_real_pos = 0.0

        self.__loop_index = 0
        ## spim properties attributes START

        self.__spim_type = 0
        self.__spim_trigger = 0
        self.__spim_xpix = 64
        self.__spim_ypix = 64
        self.__spim_sampling = [0, 0]

        ## spim properties attributes END

        self.__gun_gauge = gun.GunVacuum(SERIAL_PORT_GUN)
        if not self.__gun_gauge.success:
            from .virtual_instruments import gun_vi
            self.__gun_gauge = gun_vi.GunVacuum()

        self.__ll_gauge = al.AirLockVacuum(SERIAL_PORT_AIRLOCK)
        if not self.__ll_gauge.success:
            from .virtual_instruments import airlock_vi
            self.__ll_gauge = airlock_vi.AirLockVacuum()

    def init_handler(self):
        self.__lensInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("lenses_controller")
        self.__EELSInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("eels_spec_controller")
        self.__AperInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("diaf_controller")
        self.__StageInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            "orsay_scan_device")

        self.__EIRE = "orsay_camera_eire"
        self.__EELS = "orsay_camera_eels"

        if SLOW_PERIODIC: self.periodic()

    def stage_periodic(self):
        if not self.__stage_thread.is_alive():
            self.__stage_thread.start()

    def stage_periodic_start(self):
        counter = 0
        while counter < 10.0 / TIME_FAST_PERIODIC:
            self.stage_event.fire(self.__y_real_pos, self.__x_real_pos)
            self.property_changed_event.fire('x_stage_f')
            self.property_changed_event.fire('y_stage_f')
            time.sleep(TIME_FAST_PERIODIC)
            counter += 1
        self.__stage_thread = threading.Thread(target=self.stage_periodic_start, args=(),)

    def periodic(self):
        self.property_changed_event.fire('roa_val_f')
        self.property_changed_event.fire('voa_val_f')
        self.property_changed_event.fire('gun_vac_f')
        self.property_changed_event.fire('LL_vac_f')
        self.property_changed_event.fire('obj_cur_f')
        self.property_changed_event.fire('c1_cur_f')
        self.property_changed_event.fire('c2_cur_f')
        self.property_changed_event.fire('x_stage_f')
        self.property_changed_event.fire('y_stage_f')
        self.property_changed_event.fire('thread_cts_f')
        self.estimate_temp()
        try:
            self.append_data.fire([self.__LL_vac, self.__gun_vac, self.__obj_temp], self.__loop_index)
            self.__loop_index += 1
            if self.__loop_index == MAX_PTS: self.__loop_index = 0
            if self.__obj_temp > OBJECTIVE_MAX_TEMPERATURE and self.__obj_cur > 6.0:
                if not self.__objWarning:
                    self.__objWarning = True
                else:
                    self.shutdown_objective()
                    self.__objWarning = False
            else:
                self.__objWarning = False
        except:
            pass
        self.__thread = threading.Timer(TIME_SLOW_PERIODIC, self.periodic, args=(), )
        check = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            "orsay_scan_device")
        if not self.__thread.is_alive() and check is not None:
            self.__thread.start()

    def estimate_temp(self):
        self.__obj_temp = self.__amb_temp + ((self.__obj_res - self.__obj_res_ref) / self.__obj_res_ref) / TEMP_COEF
        if self.__obj_temp < 0: self.__obj_temp = self.__amb_temp
        self.property_changed_event.fire('obj_temp_f')

    def shutdown_objective(self):
        self.__lensInstrument.obj_global_f = False
        self.__lensInstrument.c1_global_f = False
        self.__lensInstrument.c2_global_f = False
        logging.info('*** LENSES / IVG ***: Shutdown objective lens because of high temperature.')
        if SENDMAIL:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(sender_email, 'vgStem27!')
            server.sendmail(sender_email, receiver_email, message)

    def fov_change(self, FOV):
        self.__fov = float(FOV * 1e6)  # in microns
        self.property_changed_event.fire('spim_sampling_f')
        self.property_changed_event.fire('spim_time_f')

    def warn_Scan_instrument_spim(self, value, x_pixels=0, y_pixels=0):
        # only set scan pixels if you going to start spim.
        if value: self.__OrsayScanInstrument.scan_device.set_spim_pixels = (x_pixels, y_pixels)
        self.__OrsayScanInstrument.scan_device.set_spim = value
        if value:
            self.__OrsayScanInstrument.start_playing()
        else:
            self.__OrsayScanInstrument.stop_playing()

    def warn_Scan_instrument_spim_over(self, det_data, spim_pixels, detector):
        self.spim_over.fire(det_data, spim_pixels, detector, self.__spim_sampling)

    def start_spim_push_button(self, x_pix, y_pix):
        if self.__spim_trigger == 0:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS)]
        elif self.__spim_trigger == 1:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EIRE)]
            print(now_cam)
        elif self.__spim_trigger == 2:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS), HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EIRE)]
            logging.info(
                '***IVG***: Both measurement not yet implemented. Please check back later. Using EELS instead.')

        for cam in now_cam:
            cam.stop_playing()
            cam.camera._CameraDevice__acqspimon = True
            cam.camera._CameraDevice__x_pix_spim = int(x_pix)
            cam.camera._CameraDevice__y_pix_spim = int(y_pix)
            if not cam.is_playing:
                cam.start_playing()
            else:
                logging.info('**IVG***: Please stop camera before starting spim.')

    def stop_spim_push_button(self):
        if self.__spim_trigger == 0:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS)]
        elif self.__spim_trigger == 1:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EIRE)]
        elif self.__spim_trigger == 2:
            now_cam = [HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS), HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EIRE)]
        for cam in now_cam:
            cam.stop_playing()

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***IVG***: Could not find some or all of the hardwares")
        return sendMessage

    @property
    def EHT_f(self):
        if self.__EHT == "40":
            new_value = 0
        elif self.__EHT == "60":
            new_value = 1
        elif self.__EHT == "80":
            new_value = 2
        elif self.__EHT == "100":
            new_value = 3
        return new_value

    @EHT_f.setter
    def EHT_f(self, value):
        if value == 0:
            self.__EHT = "40"
        elif value == 1:
            self.__EHT = "60"
        elif value == 2:
            self.__EHT = "80"
        elif value == 3:
            self.__EHT = "100"
        self.__set_file.settings["global_settings"]["last_HT"] = self.__EHT
        self.__set_file.save_locally()
        try:
            self.__lensInstrument.EHT_change(self.__EHT)
            self.__EELSInstrument.EHT_change(self.__EHT)
        except:
            logging.info('***IVG***: A problem happened in Lens or EELS Controller during HT change.')
        self.property_changed_event.fire('EHT_f')

    @property
    def stand_f(self):
        return self.__stand

    @stand_f.setter
    def stand_f(self, value):
        self.__stand = value
        try:
            self.__lensInstrument.obj_global_f = not value
            self.__lensInstrument.c1_global_f = not value
            self.__lensInstrument.c2_global_f = not value
        except:
            pass

        self.property_changed_event.fire('stand_f')

    @property
    def thread_cts_f(self):
        return int(threading.active_count())

    @property
    def gun_vac_f(self):
        self.__gun_vac = self.__gun_gauge.query()
        return str('{:.2E}'.format(self.__gun_vac)) + ' Torr'

    @property
    def LL_vac_f(self):
        self.__LL_vac = self.__ll_gauge.query()
        return str('{:.2E}'.format(self.__LL_vac)) + ' mBar'

    @property
    def obj_cur_f(self):
        try:
            self.__obj_cur, self.__obj_vol = self.__lensInstrument.get_values('OBJ')
            self.__obj_cur = float(self.__obj_cur.decode())
            self.__obj_vol = float(self.__obj_vol.decode())
            if self.__obj_cur > 0:
                self.__obj_res = self.__obj_vol / self.__obj_cur
            else:
                self.__obj_res = -1.
            self.property_changed_event.fire('obj_vol_f')
        except Exception as e:
            logging.info('***IVG***: A problem happened querying lens Objective value. Returning -1.0.')
            self.__obj_cur = -1.
            self.__obj_vol = -1.

        return format(self.__obj_cur, '.4f')

    @property
    def obj_vol_f(self):
        return format(self.__obj_vol, '.4f')

    @property
    def obj_temp_f(self):
        return '{:.4f}'.format(self.__obj_temp)

    @property
    def c1_cur_f(self):
        try:
            self.__c1_cur, self.__c1_vol = self.__lensInstrument.get_values('C1')
            self.__c1_cur = float(self.__c1_cur.decode())
            self.__c1_vol = float(self.__c1_vol.decode())
            if self.__c1_cur > 0:
                self.__c1_res = self.__c1_vol / self.__c1_cur
            else:
                self.__c1_res = -1.
            self.property_changed_event.fire('c1_vol_f')
            self.property_changed_event.fire('c1_res_f')
        except:
            self.__c1_cur = -1.
            self.__c1_vol = -1.
        return format(self.__c1_cur, '.3f')

    @property
    def c1_vol_f(self):
        return format(self.__c1_vol, '.3f')

    @property
    def c1_res_f(self):
        return '{:.3f}'.format(self.__c1_res)

    @property
    def c2_cur_f(self):
        try:
            self.__c2_cur, self.__c2_vol = self.__lensInstrument.get_values('C2')
            self.__c2_cur = float(self.__c2_cur.decode())
            self.__c2_vol = float(self.__c2_vol.decode())
            if self.__c2_cur > 0:
                self.__c2_res = self.__c2_vol / self.__c2_cur
            else:
                self.__c2_res = -1.
            self.property_changed_event.fire('c2_vol_f')
            self.property_changed_event.fire('c2_res_f')
        except:
            self.__c2_cur = -1.
            self.__c2_vol = -1.
        return format(self.__c2_cur, '.3f')

    @property
    def c2_vol_f(self):
        return format(self.__c2_vol, '.3f')

    @property
    def c2_res_f(self):
        return '{:.3f}'.format(self.__c2_res)

    @property
    def voa_val_f(self):
        vlist = ['None', '50 um', '100 um', '150 um', 'Error']
        try:
            self.__voa = self.__AperInstrument.voa_change_f
        except:
            self.__voa = 4

        return vlist[self.__voa]

    @property
    def roa_val_f(self):
        rlist = ['None', '50 um', '100 um', '150 um', 'Error']
        try:
            self.__roa = self.__AperInstrument.roa_change_f
        except:
            self.__roa = 4

        return rlist[self.__roa]

    @property
    def x_stage_f(self):
        try:
            tempx, _ = self.__StageInstrument.GetPos()
            if abs(tempx - self.__x_real_pos)>0.0:
                self.stage_periodic()
            self.__x_real_pos = tempx
        except:
            self.__x_real_pos = -1.e-5
        return '{:.3f}'.format(self.__x_real_pos * 1e6)

    @x_stage_f.setter
    def x_stage_f(self, value):
        self.__StageInstrument.x_pos_f = float(value) * 100.
        self.stage_periodic()
        self.property_changed_event.fire('x_stage_f')

    @property
    def y_stage_f(self):
        try:
            _, tempy = self.__StageInstrument.GetPos()
            if abs(tempy - self.__y_real_pos) > 0.0:
                self.stage_periodic()
            self.__y_real_pos = tempy
        except:
            self.__y_real_pos = -1.e-5
        return '{:.3f}'.format(self.__y_real_pos * 1e6)

    @y_stage_f.setter
    def y_stage_f(self, value):
        self.__StageInstrument.y_pos_f = float(value) * 100.
        self.stage_periodic()
        self.property_changed_event.fire('y_stage_f')

    ## spim_panel Properties START ##

    @property
    def spim_type_f(self):
        return self.__spim_type

    @spim_type_f.setter
    def spim_type_f(self, value):
        self.__spim_type = value

    @property
    def spim_trigger_f(self):
        return self.__spim_trigger

    @spim_trigger_f.setter
    def spim_trigger_f(self, value):
        self.__spim_trigger = value
        self.property_changed_event.fire('spim_time_f')

    @property
    def spim_xpix_f(self):
        return self.__spim_xpix

    @spim_xpix_f.setter
    def spim_xpix_f(self, value):
        try:
            isinstance(int(value), int)
            self.__spim_xpix = int(value)
        except ValueError:
            logging.info('***SPIM***: Please put an integer number')
        self.property_changed_event.fire('spim_xpix_f')
        self.property_changed_event.fire('spim_sampling_f')
        self.property_changed_event.fire('spim_time_f')

    @property
    def spim_ypix_f(self):
        return self.__spim_ypix

    @spim_ypix_f.setter
    def spim_ypix_f(self, value):
        try:
            isinstance(int(value), int)
            self.__spim_ypix = int(value)

        except ValueError:
            logging.info('***SPIM***: Please put an integer number')
        self.property_changed_event.fire('spim_ypix_f')
        self.property_changed_event.fire('spim_sampling_f')
        self.property_changed_event.fire('spim_time_f')

    @property
    def is_subscan_f(self):
        return str(self.__is_subscan[0])

    @is_subscan_f.setter
    def is_subscan_f(self, value):
        self.__is_subscan = value

        self.property_changed_event.fire('is_subscan_f')
        self.property_changed_event.fire('spim_sampling_f')
        self.property_changed_event.fire('spim_time_f')

    @property
    def spim_sampling_f(self):
        self.__spim_sampling = (self.__fov / self.__spim_xpix * 1e3, self.__fov / self.__spim_ypix * 1e3) if not \
        self.__is_subscan[0] else (self.__fov * self.__is_subscan[1] / self.__spim_xpix * 1e3,
                                   self.__fov * self.__is_subscan[2] / self.__spim_ypix * 1e3)
        self.__spim_sampling = [float("%.2f" % member) for member in self.__spim_sampling]
        return self.__spim_sampling

    @property
    def spim_time_f(self):
        try:
            if self.__spim_trigger == 0:
                now_cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS)
            elif self.__spim_trigger == 1:
                now_cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EIRE)
            elif self.__spim_trigger == 2:
                now_cam = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.__EELS)
                logging.info(
                    '***IVG***: Both measurement not yet implemented. Please check back later. Using EELS instead.')

            self.__spim_time = format(((
                                                   now_cam.camera.current_camera_settings.exposure_ms / 1000. + now_cam.camera.readoutTime) * self.__spim_xpix * self.__spim_ypix / 60),
                                      '.2f')
            return self.__spim_time
        except AttributeError:
            return 'None'

    ## spim_panel Properties END ##

    @property
    def live_probe_position(self):
        return self.__live_probe_position

    @live_probe_position.setter
    def live_probe_position(self, position):
        self.__live_probe_position = position
        self.property_changed_event.fire("live_probe_position")

    def _set_scan_context_probe_position(self, scan_context: stem_controller.ScanContext,
                                         probe_position: Geometry.FloatPoint) -> None:
        self.__scan_context = copy.deepcopy(scan_context)
        self.__probe_position = probe_position

    def change_pmt_gain(self, pmt_type, *, factor: float) -> None:
        scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            "orsay_scan_device")
        if scan is not None:
            if pmt_type == 0:
                self.__haadf_gain = int(scan.scan_device.orsayscan.GetPMT(1))
                self.__haadf_gain = int(self.__haadf_gain * 1.05) if factor > 1 else int(self.__haadf_gain * 0.95)
                if self.__haadf_gain > 2500: self.__haadf_gain = 2500
            if pmt_type == 1:
                self.__bf_gain = int(scan.scan_device.orsayscan.GetPMT(0))
                self.__bf_gain = int(self.__bf_gain * 1.05) if factor > 1 else int(self.__bf_gain * 0.95)
                if self.__bf_gain > 2500: self.__bf_gain = 2500
            scan.scan_device.orsayscan.SetPMT(-pmt_type + 1, self.__haadf_gain)

    def get_autostem_properties(self):
        """Return a new autostem properties (dict) to be recorded with an acquisition.
           * use property names that are lower case and separated by underscores
           * use property names that include the unit attached to the end
           * avoid using abbreviations
           * avoid adding None entries
           * dict must be serializable using json.dumps(dict)
           Be aware that these properties may be used far into the future so take care when designing additions and
           discuss/review with team members.
        """
        return {
            "high_tension": 100,
            "defocus": 60,
        }

    def change_stage_position(self, *, dy: int = None, dx: int = None):
        angle = self.__OrsayScanInstrument.scan_device.scan_rotation
        angle = angle - 22.5
        new_dx = dx*numpy.cos(numpy.radians(angle)) - dy*numpy.sin(numpy.radians(angle))
        new_dy = dx*numpy.sin(numpy.radians(angle)) + dy*numpy.cos(numpy.radians(angle))
        self.__StageInstrument.x_pos_f += dx * 1e8
        self.__StageInstrument.y_pos_f -= dy * 1e8
        self.stage_periodic()

    def TryGetVal(self, s: str) -> (bool, float):
        if s == "eels_y_offset":
            return True, 0
        elif s == "eels_x_offset":
            return True, self.__EELSInstrument.ene_offset_edit_f + self.__EELSInstrument.tare_edit_f
        elif s == "eels_y_scale":
            return True, 1
        elif s == "eels_x_scale":
            return True, self.__EELSInstrument.range_f
        else:
            return False, 0


    @property
    def is_blanked(self) -> bool:
        return self.__blanked

    @is_blanked.setter
    def is_blanked(self, value: bool) -> None:
        self.__blanked = value
        self.property_changed_event.fire("is_blanked")