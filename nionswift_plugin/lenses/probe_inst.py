# standard libraries
import logging
import time

from nion.utils import Event, Observable
from nion.swift.model import HardwareSource
try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
SERIAL_PORT = set_file.settings["lenses"]["COM"]
LAST_HT = set_file.settings["global_settings"]["last_HT"]
from . import lens_ps as lens_ps

class probeDevice(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__lenses_ps = lens_ps.Lenses(SERIAL_PORT)
        if not self.__lenses_ps.success:
            from . import lens_ps_vi
            self.__lenses_ps = lens_ps_vi.Lenses()

        self.__data = read_data.FileManager('lenses_settings')
        self.__EHT = LAST_HT
        self.__obj = 0.
        self.__c1 = 0.
        self.__c2 = 0.
        self.__objStig = [0, 0]
        self.__gunStig = [0, 0]
        self.__probeOffset = [0, 0, 0, 0]
        self.__obj_global = True
        self.__c1_global = True
        self.__c2_global = True
        self.__obj_wobbler = False
        self.__c1_wobbler = False
        self.__c2_wobbler = False
        self.wobbler_frequency_f = 2
        self.__wobbler_intensity = 0.02

        self.probe_offset0_f = 0
        self.probe_offset1_f = 0
        self.probe_offset2_f = 0
        self.probe_offset3_f = 0

    def init_handler(self):
        try:
            self.obj_edit_f = self.__data.settings[self.__EHT]["obj"]
            self.c1_edit_f = self.__data.settings[self.__EHT]["c1"]
            self.c2_edit_f = self.__data.settings[self.__EHT]['c2']
            self.obj_stigmateur0_f = self.__data.settings[self.__EHT]["obj_stig_00"]
            self.obj_stigmateur1_f = self.__data.settings[self.__EHT]["obj_stig_01"]
            self.gun_stimateur0_f = self.__data.settings[self.__EHT]["gun_stig_02"]
            self.gun_stigmateur1_f = self.__data.settings[self.__EHT]["gun_stig_03"]
        except:
            logging.info('***LENSES***: No saved values.')

        self.obj_global_f = True
        self.c1_global_f = True
        self.c2_global_f = True

    def EHT_change(self, value):
        self.__EHT = value
        self.obj_edit_f = self.__data.settings[str(value)]['obj']
        self.c1_edit_f = self.__data.settings[str(value)]['c1']
        self.c2_edit_f = self.__data.settings[str(value)]['c2']

    def save_values(self):
        self.__data.settings[self.__EHT]["obj"] = self.obj_edit_f
        self.__data.settings[self.__EHT]["c1"] = self.c1_edit_f
        self.__data.settings[self.__EHT]['c2'] = self.c2_edit_f
        self.__data.settings[self.__EHT]["obj_stig_00"] = self.obj_stigmateur0_f
        self.__data.settings[self.__EHT]["obj_stig_01"] = self.obj_stigmateur1_f
        self.__data.settings[self.__EHT]["gun_stig_02"] = self.gun_stimateur0_f
        self.__data.settings[self.__EHT]["gun_stig_03"] = self.gun_stigmateur1_f

        self.__data.save_locally()

    def get_values(self, which):
        cur, vol = self.__lenses_ps.locked_query(which)
        return cur, vol

    def get_orsay_scan_instrument(self):
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")

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
    def obj_stigmateur0_f(self):
        return self.__objStig[0]

    @obj_stigmateur0_f.setter
    def obj_stigmateur0_f(self, value):
        self.__objStig[0] = value
        self.__lenses_ps.locked_set_val(self.__objStig, 'OBJ_STIG')
        self.property_changed_event.fire('obj_stigmateur0_f')

    @property
    def obj_stigmateur1_f(self):
        return self.__objStig[1]

    @obj_stigmateur1_f.setter
    def obj_stigmateur1_f(self, value):
        self.__objStig[1] = value
        self.__lenses_ps.locked_set_val(self.__objStig, 'OBJ_STIG')
        self.property_changed_event.fire('obj_stigmateur1_f')

    @property
    def probe_offset0_f(self):
        return self.__probeOffset[0]

    @probe_offset0_f.setter
    def probe_offset0_f(self, value):
        self.__probeOffset[0] = float(value)
        read_data.InstrumentDictSetter("Probe", "CSH.u", self.__probeOffset[0] / 1e9)
        self.__lenses_ps.locked_set_val(self.__probeOffset, 'OBJ_ALIG')
        self.property_changed_event.fire('probe_offset0_f')

    @property
    def probe_offset1_f(self):
        return self.__probeOffset[1]

    @probe_offset1_f.setter
    def probe_offset1_f(self, value):
        self.__probeOffset[1] = float(value)
        self.__lenses_ps.locked_set_val(self.__probeOffset, 'OBJ_ALIG')
        self.property_changed_event.fire('probe_offset1_f')

    @property
    def probe_offset2_f(self):
        return self.__probeOffset[2]

    @probe_offset2_f.setter
    def probe_offset2_f(self, value):
        self.__probeOffset[2] = float(value)
        read_data.InstrumentDictSetter("Probe", "CSH.v", self.__probeOffset[2] / 1e9)
        self.__lenses_ps.locked_set_val(self.__probeOffset, 'OBJ_ALIG')
        self.property_changed_event.fire('probe_offset2_f')

    @property
    def probe_offset3_f(self):
        return self.__probeOffset[3]

    @probe_offset3_f.setter
    def probe_offset3_f(self, value):
        self.__probeOffset[3] = float(value)
        self.__lenses_ps.locked_set_val(self.__probeOffset, 'OBJ_ALIG')
        self.property_changed_event.fire('probe_offset3_f')

    @property
    def obj_global_f(self):
        return self.__obj_global

    @obj_global_f.setter
    def obj_global_f(self, value):
        self.__obj_global = value
        if self.__obj_wobbler: self.obj_wobbler_f = False
        if value:
            self.__lenses_ps.locked_set_val(self.__obj, 'OBJ')
        else:
            self.__lenses_ps.locked_set_val(0.0, 'OBJ')
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
            time.sleep(1.1 / self.__wobbler_frequency)
            self.obj_slider_f = self.__obj * 1e6
        self.property_changed_event.fire('obj_wobbler_f')

    @property
    def obj_slider_f(self):
        return int(self.__obj * 1e6)

    @obj_slider_f.setter
    def obj_slider_f(self, value):
        self.__obj = value / 1e6
        if self.__obj_wobbler: self.obj_wobbler_f = False
        if self.__obj_global: self.__lenses_ps.locked_set_val(self.__obj, 'OBJ')
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
        if self.__c1_wobbler: self.c1_wobbler_f = False
        if value:
            self.__lenses_ps.locked_set_val(self.__c1, 'C1')
        else:
            self.__lenses_ps.locked_set_val(0.01, 'C1')
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
            time.sleep(1.1 / self.__wobbler_frequency)
            self.c1_slider_f = self.__c1 * 1e6
        self.property_changed_event.fire('c1_wobbler_f')

    @property
    def c1_slider_f(self):
        return int(self.__c1 * 1e6)

    @c1_slider_f.setter
    def c1_slider_f(self, value):
        self.__c1 = value / 1e6
        if self.__c1_global: self.__lenses_ps.locked_set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    @property
    def c1_edit_f(self):
        return format(self.__c1, '.6f')

    @c1_edit_f.setter
    def c1_edit_f(self, value):
        self.__c1 = float(value)
        if self.__c1_global: self.__lenses_ps.locked_set_val(self.__c1, 'C1')
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    ### C2 ###

    @property
    def c2_global_f(self):
        return self.__c2_global

    @c2_global_f.setter
    def c2_global_f(self, value):
        self.__c2_global = value
        if self.__c2_wobbler: self.c2_wobbler_f = False
        if value:
            self.__lenses_ps.locked_set_val(self.__c2, 'C2')
        else:
            self.__lenses_ps.locked_set_val(0.01, 'C2')
        self.property_changed_event.fire('c2_global_f')

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
            time.sleep(1.1 / self.__wobbler_frequency)
            self.c2_slider_f = self.__c2 * 1e6
        self.property_changed_event.fire('c2_wobbler_f')

    @property
    def c2_slider_f(self):
        return int(self.__c2 * 1e6)

    @c2_slider_f.setter
    def c2_slider_f(self, value):
        self.__c2 = value / 1e6
        if self.__c2_global: self.__lenses_ps.locked_set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    @property
    def c2_edit_f(self):
        return format(self.__c2, '.6f')

    @c2_edit_f.setter
    def c2_edit_f(self, value):
        self.__c2 = float(value)
        self.__c2_global: self.__lenses_ps.locked_set_val(self.__c2, 'C2')
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    ### COND ASTIGMATORS ###
    @property
    def gun_stigmateur0_f(self):
        return self.__gunStig[0]

    @gun_stigmateur0_f.setter
    def gun_stigmateur0_f(self, value):
        self.__gunStig[0] = value
        self.__lenses_ps.locked_set_val(self.__gunStig, 'GUN_STIG')
        self.property_changed_event.fire('gun_stigmateur0_f')

    @property
    def gun_stigmateur1_f(self):
        return self.__gunStig[1]

    @gun_stigmateur1_f.setter
    def gun_stigmateur1_f(self, value):
        self.__gunStig[1] = value
        self.__lenses_ps.locked_set_val(self.__gunStig, 'GUN_STIG')
        self.property_changed_event.fire('gun_stigmateur1_f')