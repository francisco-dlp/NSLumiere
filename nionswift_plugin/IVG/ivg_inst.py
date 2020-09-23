# standard libraries
import threading
import logging
import smtplib, ssl
import os
import json

from nion.utils import Event
from nion.swift.model import HardwareSource
from nion.instrumentation import stem_controller
from nion.utils import Geometry

sender_email = "vg.lumiere@gmail.com"
receiver_email="yvesauad@gmail.com"

message="""\
Subject: Objective Lens @ VG Lumiere

This message was automatically sent and means objective lens @ VG Lum. was shutdown because of its high temperature"""


abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

DEBUG_gun = settings["IVG"]["DEBUG_GUN"]
DEBUG_airlock = settings["IVG"]["DEBUG_AIRLOCK"]
SENDMAIL = settings["IVG"]["SENDMAIL"]
FAST_PERIODIC = settings["IVG"]["FAST_PERIODIC"]["ACTIVE"]
TIME_FAST_PERIODIC=settings["IVG"]["FAST_PERIODIC"]["PERIOD"]
SLOW_PERIODIC = settings["IVG"]["SLOW_PERIODIC"]["ACTIVE"]
TIME_SLOW_PERIODIC = settings["IVG"]["SLOW_PERIODIC"]["PERIOD"]
OBJECTIVE_MAX_TEMPERATURE = settings["IVG"]["OBJECTIVE"]["MAX_TEMP"]
OBJECTIVE_RESISTANCE = settings["IVG"]["OBJECTIVE"]["RESISTANCE"]
TEMP_COEF = settings["IVG"]["OBJECTIVE"]["TEMP_COEF"]
MAX_PTS = settings["IVG"]["MAX_PTS"]
AMBIENT_TEMPERATURE = settings["IVG"]["AMBIENT_TEMPERATURE"]
EHT_INITIAL = settings["IVG"]["EHT_INITIAL"]
DEBUG_CAMERA = settings["IVG"]["CAMERA"]["DEBUG"]
CAMERA_PIXELS = settings["IVG"]["CAMERA"]["PIXELS"]
CAMERA_SIZE = settings["IVG"]["CAMERA"]["SIZE"]
DEBUG_SCAN = settings["IVG"]["DEBUG_SCAN"]

if DEBUG_gun:
    from .virtual_instruments import gun_vi as gun
else:
    from . import gun as gun

if DEBUG_airlock:
    from .virtual_instruments import airlock_vi as al
else:
    from . import airlock as al


class ivgInstrument(stem_controller.STEMController):
    def __init__(self, instrument_id: str):
        super().__init__()
        self.priority = 20
        self.instrument_id = instrument_id
        self.property_changed_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event=Event.Event()


        self.append_data=Event.Event()
        self.stage_event=Event.Event()

        self.__blanked = False
        self.__scan_context = stem_controller.ScanContext()
        self.__probe_position = None
        self.__live_probe_position = None
        self.__fov = None
        self.__obj_stig = [0, 0]
        self.__gun_stig = [0, 0]
        self.__haadf_gain = 250
        self.__bf_gain = 250


        self.__EHT=EHT_INITIAL
        self.__obj_res_ref = OBJECTIVE_RESISTANCE
        self.__amb_temp = AMBIENT_TEMPERATURE
        self.__stand=False
        self.__obj_temp=self.__amb_temp
        self.__obj_res=self.__obj_res_ref

        self.__loop_index=0

        if SLOW_PERIODIC: self.periodic()
        if FAST_PERIODIC: self.stage_periodic()

        self.__lensInstrument=None
        self.__EELSInstrument=None
        self.__AperInstrument=None
        self.__StageInstrument=None
        self.__optSpecInstrument=None
        self.__OrsayScanInstrument=None

        self.__gun_sendmessage = gun.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__gun_gauge= gun.GunVacuum(self.__gun_sendmessage)

        self.__ll_sendmessage = al.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__ll_gauge= al.AirLockVacuum(self.__ll_sendmessage)


    def get_lenses_instrument(self):
        self.__lensInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("lenses_controller")

    def get_EELS_instrument(self):
        self.__EELSInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("eels_spec_controller")

    def get_diaf_instrument(self):
        self.__AperInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("diaf_controller")

    def get_stage_instrument(self):
        self.__StageInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("stage_controller")

    def get_optSpec_instrument(self):
        self.__optSpecInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("optSpec_controller")

    def get_orsay_scan_instrument(self):
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

    def stage_periodic(self):
        self.property_changed_event.fire('x_stage_f')
        try:
            self.stage_event.fire(self.__y_real_pos, self.__x_real_pos)
        except:
            pass
        self.__stage_thread=threading.Timer(TIME_FAST_PERIODIC, self.stage_periodic, args=(),)
        if not self.__stage_thread.is_alive():
            try:
                self.__stage_thread.start()
            except:
                pass

    def periodic(self):
        self.property_changed_event.fire('roa_val_f')
        self.property_changed_event.fire('voa_val_f')
        self.property_changed_event.fire('gun_vac_f')
        self.property_changed_event.fire('LL_vac_f')
        self.property_changed_event.fire('obj_cur_f')
        self.property_changed_event.fire('c1_cur_f')
        self.property_changed_event.fire('c2_cur_f')
        self.estimate_temp()
        try:
            self.append_data.fire([self.__LL_vac, self.__gun_vac, self.__obj_temp], self.__loop_index)
            self.__loop_index+=1
            if self.__loop_index==MAX_PTS: self.__loop_index=0
            if self.__obj_temp>OBJECTIVE_MAX_TEMPERATURE and self.__obj_cur>4.0: self.shutdown_objective()
        except:
            pass
        self.__thread=threading.Timer(TIME_SLOW_PERIODIC, self.periodic, args=(),)
        if not self.__thread.is_alive():
            try:
                self.__thread.start()
            except:
                pass

    def estimate_temp(self):
        self.__obj_temp = self.__amb_temp + ((self.__obj_res-self.__obj_res_ref)/self.__obj_res_ref)/TEMP_COEF
        if self.__obj_temp<0: self.__obj_temp = self.__amb_temp
        self.property_changed_event.fire('obj_temp_f')

    def shutdown_objective(self):
        self.__lensInstrument.obj_global_f=False
        logging.info('*** LENSES / IVG ***: Shutdown objective lens because of high temperature.')
        if SENDMAIL:
            try:
                context=ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, 'vgStem27!')
                    server.sendmail(sender_email, receiver_email, message)
            except:
                pass


    def fov_change(self, FOV):
        self.__fov = float(FOV*1e6)
        try:
            self.__StageInstrument.slider_range_f=self.__fov
        except:
            pass


    def warn_instrument_spim(self, value):
        #Lets warn instrument and make instrument stop any conventional HAADF/BF order he is currently doing. I will
        #try to do spim basically creating a data_item instead of using my channels? Not sure the best approach. I
        #would love to let my ScanYves as clean as possible
        #logging.info('***IVG***: SPIM starting. Aborting (if running) HAADF/BF...')
        #try:
        if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
        self.__OrsayScanInstrument.scan_device.set_spim=value
        #except:
        #    pass




    def sendMessageFactory(self):
        def sendMessage(message):
            if message==1:
                logging.info("***IVG***: Could not find some or all of the hardwares")
            if message==3:
                logging.info("***GUN GAUGE@IVG***: Could not find hardware. Check connection.")
            if message==4:
                logging.info("***AIRLOCK GAUGE@IVG***: Could not find hardware. Check connection.")
            if message==5:
                logging.info("***GUN GAUGE@IVG***: Problem querying gun gauge. Returning zero instead. If it is an intermitent problem, you are querying too fast.")
            if message==6:
                logging.info("***AIRLOCK GAUGE@IVG***: Problem querying gun gauge. Returning zero instead.")

        return sendMessage


    @property
    def EHT_f(self):
        return self.__EHT

    @EHT_f.setter
    def EHT_f(self, value):
        self.__EHT=value
        try:
            if not self.__lensInstrument:
                self.get_lenses_instrument()
            if not self.__EELSInstrument:
                self.get_EELS_instrument()
            self.__lensInstrument.EHT_change(value)
            self.__EELSInstrument.EHT_change(value)
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
            self.__lensInstrument.obj_global_f=not value
            self.__lensInstrument.c1_global_f=not value
            self.__lensInstrument.c2_global_f=not value
        except:
            pass

        self.property_changed_event.fire('stand_f')


    @property
    def gun_vac_f(self):
        self.__gun_vac =  self.__gun_gauge.query()
        return str('{:.2E}'.format(self.__gun_vac))+' Torr'


    @property
    def LL_vac_f(self):
        self.__LL_vac=self.__ll_gauge.query()
        return str('{:.2E}'.format(self.__LL_vac))+' mBar'

    @property
    def obj_stig00_f(self):
        return int(self.__obj_stig[0] * 1e3)

    @obj_stig00_f.setter
    def obj_stig00_f(self, value):
        self.__obj_stig[0] = value / 1e3
        try:
            if not DEBUG_SCAN:
                if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
                self.__OrsayScanInstrument.scan_device.orsayscan.ObjectiveStigmateur(self.__obj_stig[0], self.__obj_stig[1])
        except:
            logging.info('***LENSES***: Could not acess objective astigmators. Please check Scan Module.')
        self.property_changed_event.fire('obj_astig00_f')

    @property
    def obj_stig01_f(self):
        return int(self.__obj_stig[1] * 1e3)

    @obj_stig01_f.setter
    def obj_stig01_f(self, value):
        self.__obj_stig[1] = value / 1e3
        try:
            if not DEBUG_SCAN:
                if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
                self.__OrsayScanInstrument.scan_device.orsayscan.ObjectiveStigmateur(self.__obj_stig[0], self.__obj_stig[1])
        except:
            logging.info('***LENSES***: Could not acess objective astigmators. Please check Scan Module.')
        self.property_changed_event.fire('obj_astig01_f')

    @property
    def gun_stig00_f(self):
        return int(self.__gun_stig[0] * 1e3)

    @gun_stig00_f.setter
    def gun_stig00_f(self, value):
        self.__gun_stig[0] = value / 1e3
        try:
            if not DEBUG_SCAN:
                if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
                self.__OrsayScanInstrument.scan_device.orsayscan.CondensorStigmateur(self.__gun_stig[0], self.__gun_stig[1])
        except:
            logging.info('***LENSES***: Could not acess gun astigmators. Please check Scan Module.')
        self.property_changed_event.fire('gun_astig00_f')

    @property
    def gun_stig01_f(self):
        return int(self.__gun_stig[1] * 1e3)

    @gun_stig01_f.setter
    def gun_stig01_f(self, value):
        self.__gun_stig[1] = value / 1e3
        try:
            if not DEBUG_SCAN:
                if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
                self.__OrsayScanInstrument.scan_device.orsayscan.CondensorStigmateur(self.__gun_stig[0], self.__gun_stig[1])
        except:
            logging.info('***LENSES***: Could not acess gun astigmators. Please check Scan Module.')
        self.property_changed_event.fire('gun_astig01_f')

    @property
    def obj_cur_f(self):
        try:
            if not self.__lensInstrument:
                self.get_lenses_instrument()
            self.__obj_cur, self.__obj_vol = self.__lensInstrument.get_values('OBJ')
            self.__obj_cur = float(self.__obj_cur.decode()[0:5])
            self.__obj_vol = float(self.__obj_vol.decode()[0:5])
            if self.__obj_cur>0:
                self.__obj_res = self.__obj_vol / self.__obj_cur
            else:
                self.__obj_res = -1.
            self.property_changed_event.fire('obj_vol_f')
            return self.__obj_cur
        except:
            logging.info('***IVG***: A problem happened Querying my Lens Objective Values. Returning 0.')
            return 0


    @property
    def obj_vol_f(self):
        return self.__obj_vol

    @property
    def obj_temp_f(self):
        return '{:.2f}'.format(self.__obj_temp)


    @property
    def c1_cur_f(self):
        try:
            if not self.__lensInstrument:
                self.get_lenses_instrument()
            self.__c1_cur, self.__c1_vol = self.__lensInstrument.get_values('C1')
            self.__c1_cur = float(self.__c1_cur.decode()[0:5])
            self.__c1_vol = float(self.__c1_vol.decode()[0:5])
            if self.__c1_cur>0:
                self.__c1_res = self.__c1_vol / self.__c1_cur
            else:
                self.__c1_res = -1.
            self.property_changed_event.fire('c1_vol_f')
            self.property_changed_event.fire('c1_res_f')
            return self.__c1_cur
        except:
            logging.info('***IVG***: A problem happened Querying my Lens C1 Values. Returning 0')
            return 0


    @property
    def c1_vol_f(self):
        return self.__c1_vol


    @property
    def c1_res_f(self):
        return '{:.2f}'.format(self.__c1_res)


    @property
    def c2_cur_f(self):
        try:
            if not self.__lensInstrument:
                self.get_lenses_instrument()
            self.__c2_cur, self.__c2_vol = self.__lensInstrument.get_values('C2')
            self.__c2_cur = float(self.__c2_cur.decode()[0:5])
            self.__c2_vol = float(self.__c2_vol.decode()[0:5])
            if self.__c2_cur>0:
                self.__c2_res = self.__c2_vol / self.__c2_cur
            else:
                self.__c2_res = -1.
            self.property_changed_event.fire('c2_vol_f')
            self.property_changed_event.fire('c2_res_f')
            return self.__c2_cur
        except:
            logging.info('***IVG***: A problem happened Querying my Lens C2 Values. Returning 0')
            return 0


    @property
    def c2_vol_f(self):
        return self.__c2_vol

    @property
    def c2_res_f(self):
        return '{:.2f}'.format(self.__c2_res)


    @property
    def voa_val_f(self):
        try:
            if not self.__AperInstrument:
                self.get_diaf_instrument()
            self.__voa=self.__AperInstrument.voa_change_f
            vlist=['None', '50 um', '100 um', '150 um']
            return vlist[self.__voa]
        except:
            logging.info('***IVG***: A problem happened Querying my VOA aperture. Returning Error')
            return 'Error'


    @property
    def roa_val_f(self):
        try:
            if not self.__AperInstrument:
                self.get_diaf_instrument()
            self.__roa=self.__AperInstrument.roa_change_f
            rlist=['None', '50 um', '100 um', '150 um']
            return rlist[self.__roa]
        except:
            logging.info('***IVG***: A problem happened Querying my VOA aperture. Returning Error')
            return 'Error'


    @property
    def x_stage_f(self):
        try:
            if not self.__StageInstrument:
                self.get_stage_instrument()
            self.__x_real_pos, self.__y_real_pos = self.__StageInstrument.GetPos()
            self.property_changed_event.fire('y_stage_f')
            return '{:.2f}'.format(self.__x_real_pos*1e6)
        except:
            logging.info('***IVG***: A problem happened Querying VG Stage. Returning 0.')
            return 0

    @property
    def y_stage_f(self):
        return '{:.2f}'.format(self.__y_real_pos*1e6)


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
        if not DEBUG_SCAN:
            if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
            if pmt_type==0:
                self.__haadf_gain = int(self.__OrsayScanInstrument.scan_device.orsayscan.GetPMT(1))
                self.__haadf_gain=int(self.__haadf_gain*1.05) if factor>1 else int(self.__haadf_gain*0.95)
                if self.__haadf_gain>2500: self.__haadf_gain=2500
            if pmt_type==1:
                self.__bf_gain = int(self.__OrsayScanInstrument.scan_device.orsayscan.GetPMT(0))
                self.__bf_gain=int(self.__bf_gain*1.05) if factor>1 else int(self.__bf_gain*0.95)
                if self.__bf_gain>2500: self.__bf_gain=2500
            self.__OrsayScanInstrument.scan_device.orsayscan.SetPMT(-pmt_type+1, self.__haadf_gain)

    def change_stage_position(self, *, dy: int=None, dx: int=None):
        self.__StageInstrument.x_pos_f+=dx*1e8
        self.__StageInstrument.y_pos_f-=dy*1e8
        self.__StageInstrument.slider_range_f=self.__fov

    def TryGetVal(self, s: str) -> (bool, float):

        try:
            if not self.__EELSInstrument:
                self.get_EELS_instrument()
            if not self.__optSpecInstrument:
                self.get_optSpec_instrument()
        except:
            pass

        if s == "eels_y_offset":
            return True, 0
        elif s == "eels_x_offset":
            return True, self.__EELSInstrument.ene_offset_edit_f
        elif s == "eels_y_scale":
            return True, 1
        elif s == "eels_x_scale":
            return True, self.__EELSInstrument.range_f

        if s == "eire_y_offset":
            return True, 0
        elif s == "eire_x_offset":
            return True, (self.__optSpecInstrument.wav_f - self.__optSpecInstrument.dispersion_f * CAMERA_SIZE / 2.)
        elif s == "eire_y_scale":
            return True, 1
        elif s == "eire_x_scale":
            return True, self.__optSpecInstrument.dispersion_f * CAMERA_SIZE / CAMERA_PIXELS

        else:
            return False, 0

    @property
    def is_blanked(self) -> bool:
        return self.__blanked

    @is_blanked.setter
    def is_blanked(self, value: bool) -> None:
        self.__blanked = value
        self.property_changed_event.fire("is_blanked")


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
            "high_tension_v": self.voltage,
            "defocus_m": self.defocus_m,
        }


