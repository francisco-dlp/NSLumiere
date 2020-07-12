# standard libraries
import json
import os
import logging
import time

from nion.utils import Event
from nion.utils import Observable
from nion.swift.model import HardwareSource

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)


DEBUG = settings["lenses"]["DEBUG"]

if DEBUG:
    from . import lens_ps_vi as lens_ps
else:
    from . import lens_ps as lens_ps



class probeDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__sendmessage = lens_ps.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__lenses_ps = lens_ps.Lenses(self.__sendmessage)

        self.__obj = 0.
        self.__c1 = 0.
        self.__c2 = 0.
        self.__obj_global = True
        self.__c1_global = True
        self.__c2_global = True
        self.__obj_wobbler = False
        self.__c1_wobbler = False
        self.__c2_wobbler = False
        self.wobbler_frequency_f = 2
        self.__wobbler_intensity = 0.05

        self.__obj_astig = [0, 0]
        self.__cond_astig = [0, 0]

        self.__OrsayScanInstrument=HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device") ## does not always work. Put it again in property...

        try:
            inst_dir = os.path.dirname(__file__)
            abs_path = os.path.join(inst_dir, 'lenses_settings.json')
            with open(abs_path) as savfile:
                data = json.load(savfile)  # data is load json
            logging.info(json.dumps(data, indent=4))
            self.obj_edit_f = data["3"]["obj"]
            self.c1_edit_f = data["3"]["c1"]
            self.c2_edit_f = data["3"]['c2']
            self.obj_astig00_f=data["3"]["obj_stig_00"]
            self.obj_astig01_f=data["3"]["obj_stig_01"]
            self.cond_astig02_f=data["3"]["cond_stig_02"]
            self.cond_astig03_f=data["3"]["cond_stig_03"]
        except:
            logging.info('***LENSES***: No saved values.')

        self.obj_global_f = True
        self.c1_global_f = True
        self.c2_global_f = True

    def EHT_change(self, value):
        inst_dir = os.path.dirname(__file__)
        abs_path = os.path.join(inst_dir, 'lenses_settings.json')
        with open(abs_path) as savfile:
            data = json.load(savfile)  # data is load json
        self.obj_edit_f = data[str(value)]['obj']
        self.c1_edit_f = data[str(value)]['c1']
        self.c2_edit_f = data[str(value)]['c2']

    def get_values(self, which):
        cur, vol = self.__lenses_ps.query(which)
        return cur, vol

    def get_orsay_scan_instrument(self):
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***LENSES***: Could not find Lenses PS")
            if message == 2:
                logging.info("***LENSES***: Attempt to set values out of range.")
            if message == 4:
                logging.info('***LENSES***: Communication Error over Serial Port. Easy check using Serial Port '
                             'Monitor software.')

        return sendMessage

    ### General ###

    @property
    def wobbler_frequency_f(self):
        return self.__wobbler_frequency

    @wobbler_frequency_f.setter
    def wobbler_frequency_f(self, value):
        self.__wobbler_frequency = value
        if self.__obj_wobbler: self.obj_wobbler_f = False
        if self.__c1_wobbler: self.c1_wobbler_f = False
        if self.__c2_wobbler: self.c2_wobbler_f = False
        self.property_changed_event.fire("wobbler_frequency_f")

    @property
    def wobbler_intensity_f(self):
        return self.__wobbler_intensity

    @wobbler_intensity_f.setter
    def wobbler_intensity_f(self, value):
        self.__wobbler_intensity = float(value)
        if self.__obj_wobbler:
            self.obj_wobbler_f = False
            self.obj_wobbler_f = True
        if self.__c1_wobbler:
            self.c1_wobbler_f = False
            self.c1_wobbler_f = True
        if self.__c2_wobbler:
            self.c2_wobbler_f = False
            self.c2_wobbler_f = True
        self.property_changed_event.fire("wobbler_intensity_f")

    ### OBJ ###

    @property
    def obj_astig00_f(self):
        return int(self.__obj_astig[0]*1e3)

    @obj_astig00_f.setter
    def obj_astig00_f(self, value):
        self.__obj_astig[0] = value/1e3
        try:
            if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
            self.__OrsayScanInstrument.scan_device.orsayscan.ObjectiveStigmateur(self.__obj_astig[0], self.__obj_astig[1])
            #self.__OrsayScanInstrument.scan_device.obj_stig=self.__obj_astig
        except:
            logging.info('***LENSES***: Could not acess objective astigmators. Please check Scan Module.')
        self.property_changed_event.fire('obj_astig00_f')

    @property
    def obj_astig01_f(self):
        return int(self.__obj_astig[1]*1e3)

    @obj_astig01_f.setter
    def obj_astig01_f(self, value):
        self.__obj_astig[1] = value/1e3
        try:
            if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
            self.__OrsayScanInstrument.scan_device.orsayscan.ObjectiveStigmateur(self.__obj_astig[0], self.__obj_astig[1])
        except:
            logging.info('***LENSES***: Could not acess objective astigmators. Please check Scan Module.')
        self.property_changed_event.fire('obj_astig01_f')

    @property
    def obj_global_f(self):
        return self.__obj_global

    @obj_global_f.setter
    def obj_global_f(self, value):
        self.__obj_global = value
        if value:
            self.__lenses_ps.set_val(self.__obj, 'OBJ')
        else:
            self.__lenses_ps.set_val(0.0, 'OBJ')
        self.property_changed_event.fire('obj_global_f')

    @property
    def obj_wobbler_f(self):
        return self.__obj_wobbler

    @obj_wobbler_f.setter
    def obj_wobbler_f(self, value):
        self.__obj_wobbler = value
        if value:
            if self.__c1_wobbler: self.c1_wobbler_f = False
            if self.__c2_wobbler: self.c2_wobbler_f = False
            self.__lenses_ps.wobbler_on(self.__obj, self.__wobbler_intensity, self.__wobbler_frequency, 'OBJ')
        else:
            self.__lenses_ps.wobbler_off()
            time.sleep(2.5 / self.__wobbler_frequency)
            self.obj_slider_f = self.__obj * 1e6
        self.property_changed_event.fire('obj_wobbler_f')

    @property
    def obj_slider_f(self):
        return int(self.__obj * 1e6)

    @obj_slider_f.setter
    def obj_slider_f(self, value):
        self.__obj = value / 1e6
        if self.__obj_wobbler: self.obj_wobbler_f = False
        if self.__obj_global: self.__lenses_ps.set_val(self.__obj, 'OBJ')
        # if self.__obj_global: threading.Thread(target=self.__lenses_ps.set_val, args=(self.__obj, 'OBJ'),).start()
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")

    @property
    def obj_edit_f(self):
        return format(self.__obj, '.6f')

    @obj_edit_f.setter
    def obj_edit_f(self, value):
        self.__obj = float(value)
        # if self.__obj_global: self.__lenses_ps.set_val(self.__obj, 'OBJ')
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")

    ### C1 ###

    @property
    def c1_global_f(self):
        return self.__c1_global

    @c1_global_f.setter
    def c1_global_f(self, value):
        self.__c1_global = value
        if value:
            self.__lenses_ps.set_val(self.__c1, 'C1')
        else:
            self.__lenses_ps.set_val(0.01, 'C1')
        self.property_changed_event.fire('c1_global_f')

    @property
    def c1_wobbler_f(self):
        return self.__c1_wobbler

    @c1_wobbler_f.setter
    def c1_wobbler_f(self, value):
        self.__c1_wobbler = value
        if value:
            if self.__obj_wobbler: self.obj_wobbler_f = False
            if self.__c2_wobbler: self.c2_wobbler_f = False
            self.__lenses_ps.wobbler_on(self.__c1, self.__wobbler_intensity, self.__wobbler_frequency, 'C1')
        else:
            self.__lenses_ps.wobbler_off()
            time.sleep(2.5 / self.__wobbler_frequency)
            self.c1_slider_f = self.__c1 * 1e6
        self.property_changed_event.fire('c1_wobbler_f')

    @property
    def c1_slider_f(self):
        return int(self.__c1 * 1e6)

    @c1_slider_f.setter
    def c1_slider_f(self, value):
        self.__c1 = value / 1e6
        if self.__c1_global: self.__lenses_ps.set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    @property
    def c1_edit_f(self):
        return format(self.__c1, '.6f')

    @c1_edit_f.setter
    def c1_edit_f(self, value):
        self.__c1 = float(value)
        if self.__c1_global: self.__lenses_ps.set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    ### C2 ###

    @property
    def c2_global_f(self):
        return self.__c2_global

    @c2_global_f.setter
    def c2_global_f(self, value):
        self.__c2_global = value
        if value:
            self.__lenses_ps.set_val(self.__c2, 'C2')
        else:
            self.__lenses_ps.set_val(0.01, 'C2')
        self.property_changed_event.fire('c2_global_setter')

    @property
    def c2_wobbler_f(self):
        return self.__c2_wobbler

    @c2_wobbler_f.setter
    def c2_wobbler_f(self, value):
        self.__c2_wobbler = value
        if value:
            if self.__obj_wobbler: self.obj_wobbler_f = False
            if self.__c1_wobbler: self.c1_wobbler_f = False
            self.__lenses_ps.wobbler_on(self.__c2, self.__wobbler_intensity, self.__wobbler_frequency, 'C2')
        else:
            self.__lenses_ps.wobbler_off()
            time.sleep(2.5 / self.__wobbler_frequency)
            self.c2_slider_f = self.__c2 * 1e6
        self.property_changed_event.fire('c2_wobbler_f')

    @property
    def c2_slider_f(self):
        return int(self.__c2 * 1e6)

    @c2_slider_f.setter
    def c2_slider_f(self, value):
        self.__c2 = value / 1e6
        if self.__c2_global: self.__lenses_ps.set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    @property
    def c2_edit_f(self):
        return format(self.__c2, '.6f')

    @c2_edit_f.setter
    def c2_edit_f(self, value):
        self.__c2 = float(value)
        self.__c2_global: self.__lenses_ps.set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    ### COND ASTIGMATORS ###

    @property
    def cond_astig02_f(self):
        return int(self.__cond_astig[0]*1e3)

    @cond_astig02_f.setter
    def cond_astig02_f(self, value):
        self.__cond_astig[0] = value/1e3
        try:
            if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
            self.__OrsayScanInstrument.scan_device.orsayscan.CondensorStigmateur(self.__cond_astig[0], self.__cond_astig[1])
        except:
            logging.info('***LENSES***: Could not acess gun astigmators. Please check Scan Module.')
        self.property_changed_event.fire('cond_astig02_f')

    @property
    def cond_astig03_f(self):
        return int(self.__cond_astig[1]*1e3)

    @cond_astig03_f.setter
    def cond_astig03_f(self, value):
        self.__cond_astig[1] = value/1e3
        try:
            if not self.__OrsayScanInstrument: self.get_orsay_scan_instrument()
            self.__OrsayScanInstrument.scan_device.orsayscan.CondensorStigmateur(self.__cond_astig[0], self.__cond_astig[1])
        except:
            logging.info('***LENSES***: Could not acess gun astigmators. Please check Scan Module.')
        self.property_changed_event.fire('cond_astig03_f')
