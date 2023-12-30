# standard libraries
import threading, logging, smtplib, time, numpy, copy, typing

from nion.instrumentation import HardwareSource, stem_controller, scan_base
from nion.utils import Registry, Geometry, Event

try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

sender_email = "vg.lumiere@gmail.com"
receiver_email = "yvesauad@gmail.com"

message = """\
Subject: Objective Lens @ VG Lumiere

This message was automatically sent and means objective lens @ VG Lum. was shutdown because of its high temperature"""



set_file = read_data.FileManager('global_settings')

SERIAL_PORT_GUN = set_file.settings["OrsayInstrument"]["COM_GUN"]
SERIAL_PORT_AIRLOCK = set_file.settings["OrsayInstrument"]["COM_AIRLOCK"]
SLOW_PERIODIC = set_file.settings["OrsayInstrument"]["SLOW_PERIODIC"]

SENDMAIL = 0
TIME_SLOW_PERIODIC = 1.0
OBJECTIVE_MAX_TEMPERATURE = 60.0
OBJECTIVE_RESISTANCE = 5.18
TEMP_COEF = 0.004041
MAX_PTS = 5000
TOTAL_TIME_FAST_PERIODIC = 5.0
TIME_FAST_PERIODIC = 0.2

from . import gun as gun
from . import airlock as al

class Control():
    def __init__(self):
        pass

class InstrumentControl():
    def __init__(self):
        self.controls = dict()
        self.detailed_controls = dict()

    def __getattr__(self, name):
        return self[name]

    def update_control(self, key: str, value):
        self.controls[key] = value

    def update_control_detailed(self, type: str, key: str, value):
        self.controls[key] = value
        if type not in self.detailed_controls.keys():
            self.detailed_controls[type] = dict()
        self.detailed_controls[type][key] = value

    def get_control(self, key):
        try:
            return [True, self.controls[key]]
        except:
            logging.info(f'**InstrumentControl***: Could not found controller value {key}. Creating default value as 1.')
            self.update_control(key, 1)
            return [True, self.controls[key]]

    def as_dict(self):
        return self.controls

    def as_dict_detailed(self):
        return self.detailed_controls


class ivgInstrument(stem_controller.STEMController):
    def __init__(self, instrument_id: str):
        super().__init__()
        self.priority = 25
        self.instrument_id = instrument_id
        self.__scan_controller = None
        self.property_changed_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()
        self.append_data = Event.Event()
        self.stage_event = Event.Event()

        self.__set_file = read_data.FileManager('global_settings')
        self.controls = InstrumentControl()

        self.__blanked = False
        self.__running = True
        self.__scan_context = stem_controller.ScanContext()
        self.__probe_position = None
        self.__live_probe_position = None
        self.__fov = 4.0 #Begin fov as 4.0 microns
        self.__haadf_gain = 250
        self.__bf_gain = 250

        self.__EHT = self.__set_file.settings["global_settings"]["last_HT"]
        self.__obj_res_ref = OBJECTIVE_RESISTANCE
        self.__amb_temp = 23
        self.__stand = False
        self.__stage_moving = [False, False] #x and y stage moving
        self.__stage_thread = threading.Thread(target=self.stage_periodic_start, args=(),)
        self.__x_real_pos = self.__y_real_pos = 0.0

        self.__objWarning = False
        self.__obj_temp = self.__amb_temp
        self.__obj_res = self.__obj_res_ref
        self.__c1_vol = self.__c1_res = self.__c2_vol = self.__c2_res = 0.0



        self.__loop_index = 0

        #Checking if auto_stem is here. This is to control ChromaTEM
        AUTOSTEM_CONTROLLER_ID = "autostem_controller"
        self.__isChromaTEM = False
        try:
            autostem = HardwareSource.HardwareSourceManager().get_instrument_by_id(AUTOSTEM_CONTROLLER_ID)
            if autostem != None:
                tuning_manager = autostem.tuning_manager
                self.__instrument = tuning_manager.instrument_controller
                self.__isChromaTEM = True
        except AttributeError:
            logging.info('**IVG***: Issue finding hardwareSource. If you are in a Nion microscope please fix this.')

        self.__gun_gauge = gun.GunVacuum(SERIAL_PORT_GUN)
        if not self.__gun_gauge.success:
            from .virtual_instruments import gun_vi
            self.__gun_gauge = gun_vi.GunVacuum()

        self.__ll_gauge = al.AirLockVacuum(SERIAL_PORT_AIRLOCK)
        if not self.__ll_gauge.success:
            from .virtual_instruments import airlock_vi
            self.__ll_gauge = airlock_vi.AirLockVacuum()

    def init_handler(self):
        self.__lensInstrument = Registry.get_component("lenses_controller")
        self.__EELSInstrument = Registry.get_component("eels_spec_controller")
        self.__AperInstrument = Registry.get_component("diaf_controller")
        self.__StageInstrument = Registry.get_component("stage_controller")

        if SLOW_PERIODIC: self.periodic()

    @property
    def scan_controller(self) -> typing.Optional[scan_base.ScanHardwareSource]:
        # for testing
        if self.__scan_controller:
            return self.__scan_controller
        # prefer the primary scan_hardware_source. this is implemented a bit funny for
        # backwards compatibility, with reverse logic.
        for component in Registry.get_components_by_type("scan_hardware_source"):
            scan_hardware_source = typing.cast("scan_base.ScanHardwareSource", component)
            if scan_hardware_source.hardware_source_id == "open_scan_device":
                self.__scan_controller = scan_hardware_source
                return scan_hardware_source
            if self.__scan_controller is None and scan_hardware_source.hardware_source_id == "orsay_scan_device":
                self.__scan_controller = scan_hardware_source
        return self.__scan_controller

    def stage_periodic(self):
        if not self.__stage_thread.is_alive():
            self.__stage_thread.start()

    def stage_periodic_start(self):
        counter = 0
        while counter < TOTAL_TIME_FAST_PERIODIC / TIME_FAST_PERIODIC:
            self.stage_event.fire(self.__y_real_pos, self.__x_real_pos)
            self.property_changed_event.fire('x_stage_f')
            self.property_changed_event.fire('y_stage_f')
            time.sleep(TIME_FAST_PERIODIC)
            counter += 1
        self.__stage_thread = threading.Thread(target=self.stage_periodic_start, args=(),)

    def close(self):
        self.__running = False

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
        if not self.__thread.is_alive() and self.__running:
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
        #Magic function. Uncomment for switching between superscan and vg scan main subscan choice.
        self.__fov = float(FOV * 1e6)  # in microns
        if self.__isChromaTEM:
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "superscan")
            d = scan.get_frame_parameters(0)
            #d.fov_nm = FOV * 1e9
            #scan.set_frame_parameters(0, d)
        self.property_changed_event.fire('spim_sampling_f')
        self.property_changed_event.fire('spim_time_f')

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
            self.__EELSInstrument.EHT_change(self.__EHT)
        except:
            logging.info('***IVG***: A problem happened in EELS Controller during HT change.')

        try:
            self.__lensInstrument.EHT_change(self.__EHT)
        except:
            logging.info('***IVG***: A problem happened in lens Controller during HT change.')

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
        read_data.InstrumentDictSetter("Vaccum", "gun_vac_f", self.__gun_vac)
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
        return self.controls.as_dict_detailed()

    def change_stage_position(self, *, dy: int = None, dx: int = None):
        if self.__isChromaTEM:
            self.__instrument.change_stage_position(dy=dy, dx=dx)
        else:
            scan = self.scan_controller
            STAGE_REFERENCE_ANGLE = float(self.__set_file.settings["stage"]["REFERENCE_ANGLE"])
            angle = scan.scan_device.scan_rotation
            angle = angle - STAGE_REFERENCE_ANGLE
            new_dx = dx*numpy.cos(numpy.radians(angle)) - dy*numpy.sin(numpy.radians(angle))
            new_dy = dx*numpy.sin(numpy.radians(angle)) + dy*numpy.cos(numpy.radians(angle))
            self.__StageInstrument.x_pos_edit_f = float(self.__StageInstrument.x_pos_edit_f) + 1.0 * new_dx * 1e6
            self.__StageInstrument.y_pos_edit_f = float(self.__StageInstrument.y_pos_edit_f) - 1.0 * new_dy * 1e6
            self.stage_periodic()

    def SetValDetailed(self, type, s, val):
        self.controls.update_control_detailed(type, s, val)

    def SetVal(self, s, val):
        if self.__isChromaTEM:
            self.__instrument.SetVal(s, val)
        else:
            self.controls.update_control(s, val)
        # if s in self.__EIRE_Controls.keys():
        #     if s == 'eire_x_scale':
        #         val = val * 2e2
        #     self.__EIRE_Controls[s] = val
        # elif s == 'DriftRate.u':
        #     self.__driftRate[0] = val
        # elif s == 'DriftRate.v':
        #     self.__driftRate[1] = val
        # elif s == "CSH.u":
        #     self.__csh[0] = val #in nanometers
        #     self.__lensInstrument.probe_offset0_f = int(val * 1e9)
        # elif s == "CSH.v":
        #     self.__csh[1] = val #in nanometers
        #     self.__lensInstrument.probe_offset2_f = int(val * 1e9)
        # elif s == "DriftCorrectionUpdateInterval":
        #     self.__driftCorrectionUpdateInterval = val
        # elif s == "DriftMeasureTime":
        #     self.__driftMeasureTime = val
        # elif s == "DriftTimeConstant":
        #     self.__driftTimeConstant = val
        # elif s == "MaxShifterRange":
        #     self.__maxShifterRange = val
        # elif s == "DiftAutoStopThreshold":
        #     self.__diftAutoStopThreshold = val
        # elif s == "ResetShiftersToOpposite":
        #     self.__resetShiftersToOpposite = val
        # else:
        #     logging.info(f'**IVG***: Could not found controller {s} with value {val} in SetVal.')
        # return True

    # def InformControl(self, s, val):
    #     if s=='DriftRate.u':
    #         self.__driftRate[0] = val
    #         self.__driftCompensation[0] = val
    #     elif s == 'DriftRate.v':
    #         self.__driftRate[1] = val
    #         self.__driftCompensation[1] = val
    #     return True

    # def SetValAndConfirm(self, s, val, tolfactor, timeout_ms):
    #     if s == "CSH.u":
    #         pass
    #         #self.__lensInstrument.probe_offset0_f += int(self.__calib[0] * (1-val)*1e9)
    #     elif s == "CSH.v":
    #         self.__csh[1] = val
    #
    #         #Setting up X
    #         num = self.__calib[3] * (1 - self.__csh[0]) * 1e9 - self.__calib[1] * (1 - self.__csh[1]) * 1e9
    #         den = self.__calib[0] * self.__calib[3] - self.__calib[2] * self.__calib[1]
    #         self.__lensInstrument.probe_offset0_f += int(num/den)
    #
    #         # Setting up Y
    #         num = self.__calib[2] * (1 - self.__csh[0]) * 1e9 - self.__calib[0] * (1 - self.__csh[1]) * 1e9
    #         den = self.__calib[1] * self.__calib[2] - self.__calib[0] * self.__calib[3]
    #         self.__lensInstrument.probe_offset2_f += int(num / den)
    #         #self.__lensInstrument.probe_offset1_f += int(self.__calib[1] * (1-val)*1e9)
    #     return True

    def TryGetVal(self, s: str) -> (bool, float):
        if self.__isChromaTEM:
            return self.__instrument.TryGetVal(s)
        else:
            return self.controls.get_control(s)
        # if s in self.__EIRE_Controls.keys():
        #     return True, self.__EIRE_Controls[s]
        # elif s == "eels_y_offset":
        #     return True, 0
        # elif s == "KURO_EELS_eVOffset":
        #     try:
        #         return True, self.__EELSInstrument.ene_offset_edit_f + self.__EELSInstrument.tare_edit_f
        #     except AttributeError:
        #         return True, 0
        # elif s == "eels_y_scale":
        #     return True, 1
        # elif s == "EELS_TV_eVperpixel":
        #     try:
        #         return True, self.__EELSInstrument.range_f
        #     except AttributeError:
        #         return True, 1
        # elif s == "Princeton_CL_nmOffset":
        #     return True, 1
        # elif s == "Princeton_CL_nmperpixel":
        #     return True, 1
        # elif s == "Princeton_CL_radsperpixel":
        #     return True, 1
        # elif s == "CSH.u":
        #     return True, self.__lensInstrument.probe_offset0_f / 1e9
        # elif s == "CSH.v":
        #     return True, self.__lensInstrument.probe_offset2_f / 1e9
        # elif s == "DriftCompensation.u":
        #     return True, self.__driftCompensation[0]
        # elif s == "DriftCompensation.v":
        #     return True, self.__driftCompensation[1]
        # elif s == "DriftCorrectionUpdateInterval":
        #     return True, self.__driftCorrectionUpdateInterval
        # elif s == "DriftMeasureTime":
        #     return True, self.__driftMeasureTime
        # elif s == "DriftCcorrThreshold":
        #     return True, 0.1
        # elif s == "DriftTimeConstant":
        #     return True, self.__driftTimeConstant
        # elif s == "MaxShifterRange":
        #     return True, self.__maxShifterRange
        # elif s == "DiftAutoStopThreshold":
        #     return True, self.__diftAutoStopThreshold
        # elif s == "ResetShiftersToOpposite":
        #     return True, self.__resetShiftersToOpposite
        # else:
        #     logging.info(f'**IVG***: Could not found controller value {s} in TryGetVal.')
        #     return True, 1

    @property
    def is_blanked(self) -> bool:
        return self.__blanked

    @is_blanked.setter
    def is_blanked(self, value: bool) -> None:
        self.__blanked = value
        self.property_changed_event.fire("is_blanked")