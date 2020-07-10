# standard libraries
import threading
import logging
import smtplib, ssl
import os
import json

from nion.utils import Event
from nion.utils import Observable
from nion.swift.model import HardwareSource

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


if DEBUG_gun:
    from . import gun_vi as gun
else:
    from . import gun as gun

if DEBUG_airlock:
    from . import airlock_vi as al
else:
    from . import airlock as al


class ivgDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event=Event.Event()
        
        self.append_data=Event.Event()
        self.stage_event=Event.Event()
        
        self.__EHT=EHT_INITIAL
        self.__obj_res_ref = OBJECTIVE_RESISTANCE
        self.__amb_temp = AMBIENT_TEMPERATURE

        self.__obj_temp=self.__amb_temp
        self.__obj_res=self.__obj_res_ref

        self.__loop_index=0

        if SLOW_PERIODIC: self.periodic()
        if FAST_PERIODIC: self.stage_periodic()

        self.__lensInstrument=None
        self.__EELSInstrument=None
        self.__AperInstrument=None
        self.__StageInstrument=None

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

    def stage_periodic(self):
        self.property_changed_event.fire('x_stage_f')
        try:
            self.stage_event.fire(self.__y_real_pos, self.__x_real_pos)
        except:
            logging.info('***IVG***: Could not sent [FAST] periodic values to the panel.')
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
            if self.__obj_temp>OBJECTIVE_MAX_TEMPERATURE: self.shutdown_objective()
        except:
            logging.info('***IVG***: Could not sent [SLOW] periodic values to the panel.')
        self.__thread=threading.Timer(TIME_SLOW_PERIODIC, self.periodic, args=(),)
        if not self.__thread.is_alive():
            try:
                self.__thread.start()
            except:
                pass
        
    def estimate_temp(self):
        self.__obj_temp = self.__amb_temp + ((self.__obj_res-self.__obj_res_ref)/self.__obj_res_ref)/TEMP_COEF
        self.property_changed_event.fire('obj_temp_f')

    def shutdown_objective(self):
        #self.__lensInstrument.obj_global_f=False
        #logging.info('*** LENSES / IVG ***: Shutdown objective lens because of high temperature.')
        if SENDMAIL:
            try:
                context=ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, 'vgStem27!')
                    server.sendmail(sender_email, receiver_email, message)
            except:
                pass


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
    def gun_vac_f(self):
        self.__gun_vac =  self.__gun_gauge.query()
        return str('{:.2E}'.format(self.__gun_vac))+' Torr'


    @property
    def LL_vac_f(self):
        self.__LL_vac=self.__ll_gauge.query()
        return str('{:.2E}'.format(self.__LL_vac))+' mBar'

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
