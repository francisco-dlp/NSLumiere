# standard libraries
import json
import os
import logging
import time

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath('C:\ProgramData\Microscope\global_settings.json')
try:
    with open(abs_path) as savfile:
        settings = json.load(savfile)
    SERIAL_PORT = settings["EELS"]["COM"]
except FileNotFoundError:
    logging.info('***EELS SPEC***: No file found in Microscope main folder. Searching locally...')
    abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/global_settings.json')
    with open(abs_path) as savfile:
        settings = json.load(savfile)
    SERIAL_PORT = settings["EELS"]["COM"]

from . import eels_spec as spec

class EELS_SPEC_Device(Observable.Observable):

    def __init__(self, nElem, ElemNames):
        self.property_changed_event = Event.Event()
        self.reset_slider = Event.Event()

        self.__eels_spec = spec.EELS_Spectrometer(SERIAL_PORT)
        self.is_vsm = self.__eels_spec.vsm_success
        self.is_spec = self.__eels_spec.serial_success
        if not self.__eels_spec.success:
            from . import eels_spec_vi as spec_vi
            self.__eels_spec = spec_vi.EELS_Spectrometer()

        self.__elem = [0] * nElem
        self.__names = ElemNames
        assert len(self.__names)==nElem

        self.__zlpTare = 0.0

        self.__focus_wobbler_int=250
        self.__dispersion_wobbler_int=250
        self.__focus_wobbler_index = 0
        self.__dispersion_wobbler_index = 0
        self.__vsm_wobbler = False

        self.__EHT = '3'

        try:
            abs_path = os.path.abspath('C:\ProgramData\Microscope\eels_settings.json')
            try:
                with open(abs_path) as savfile:
                    data = json.load(savfile)
            except FileNotFoundError:
                abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/eels_settings.json')
                with open(abs_path) as savfile:
                    data = json.load(savfile)
            self.__dispIndex = int(data["3"]["last"])
            self.disp_change_f = self.__dispIndex  # put last index

        except:
            logging.info('***EELS SPEC***: No saved values.')

    def init_handler(self):
        self.focus_wobbler_f=0
        self.dispersion_wobbler_f=0
        self.disp_change_f = self.__dispIndex  # put last index
        self.ene_offset_f = 0 #putting VSM back to zero
        return  (self.is_vsm, self.is_spec)


    def set_spec_values(self, value):
        abs_path = os.path.abspath('C:\ProgramData\Microscope\eels_settings.json')
        try:
            with open(abs_path) as savfile:
                data = json.load(savfile)
        except FileNotFoundError:
            abs_path = os.path.join(os.path.dirname(__file__), '../aux_files/config/eels_settings.json')
            with open(abs_path) as savfile:
                data = json.load(savfile)

        self.range_f = data[self.__EHT][value]['range']
        self.note_f = data[self.__EHT][value]['note']
        self.fx_slider_f = int(data[self.__EHT][value]['fx'])
        self.fy_slider_f = int(data[self.__EHT][value]['fy'])
        self.sx_slider_f = int(data[self.__EHT][value]['sx'])
        self.sy_slider_f = int(data[self.__EHT][value]['sy'])
        self.dy_slider_f = int(data[self.__EHT][value]['dy'])
        self.q1_slider_f = int(data[self.__EHT][value]['q1'])
        self.q2_slider_f = int(data[self.__EHT][value]['q2'])
        self.q3_slider_f = int(data[self.__EHT][value]['q3'])
        self.q4_slider_f = int(data[self.__EHT][value]['q4'])
        self.dx_slider_f = int(data[self.__EHT][value]['dx'])
        self.dmx_slider_f = int(data[self.__EHT][value]['dmx'])

    def EHT_change(self, value):
        self.__EHT = str(
            value)  # next set at disp_change_f will going to be with the new self__EHT. Nice way of doing it
        self.disp_change_f = self.__dispIndex

    """
    General Properties
    """

    @property
    def range_f(self):
        return self.__range

    @range_f.setter
    def range_f(self, value):
        self.__range = value
        self.property_changed_event.fire('range_f')

    @property
    def note_f(self):
        return self.__note

    @note_f.setter
    def note_f(self, value):
        self.__note=value
        self.property_changed_event.fire('note_f')

    @property
    def disp_change_f(self):
        return self.__dispIndex

    @disp_change_f.setter
    def disp_change_f(self, value):
        self.reset_slider.fire()
        self.__dispIndex = value
        self.set_spec_values(str(value))
        self.property_changed_event.fire('disp_change_f')

    """
    Wobbler Settings
    """

    @property
    def focus_wobbler_f(self):
        return self.__focus_wobbler_index

    @focus_wobbler_f.setter
    def focus_wobbler_f(self, value):
        focus_list = ['OFF', self.__names[0], self.__names[1], self.__names[2], self.__names[3], self.__names[4]]
        focus_list_values=[0, self.__elem[0], self.__elem[1], self.__elem[2], self.__elem[3], self.__elem[4]]
        self.__focus_wobbler_index = value
        if bool(value):
            self.__eels_spec.wobbler_on(focus_list_values[value], self.__focus_wobbler_int, focus_list[value])
        else:
            self.__eels_spec.wobbler_off()
        self.property_changed_event.fire('focus_wobbler_f')

    @property
    def focus_wobbler_int_f(self):
        return self.__focus_wobbler_int

    @focus_wobbler_int_f.setter
    def focus_wobbler_int_f(self, value):
        self.__focus_wobbler_int = int(value)
        self.property_changed_event.fire('focus_wobbler_int_f')

    @property
    def dispersion_wobbler_f(self):
        return self.__dispersion_wobbler_index

    @dispersion_wobbler_f.setter
    def dispersion_wobbler_f(self, value):
        disp_list = ['OFF', self.__names[5], self.__names[6], self.__names[7], self.__names[8], self.__names[9], self.__names[10]]
        disp_list_values = [0, self.__elem[5], self.__elem[6], self.__elem[7], self.__elem[8], self.__elem[9], self.__elem[10]]
        self.__dispersion_wobbler_index = value
        if value:
            self.__eels_spec.wobbler_on(disp_list_values[value], self.__dispersion_wobbler_int, disp_list[value])
        else:
            self.__eels_spec.wobbler_off()
            self.q1_slider_f=self.__elem[5]
            self.q2_slider_f = self.__elem[6]
            self.q3_slider_f = self.__elem[7]
            self.q4_slider_f = self.__elem[8]
            self.dx_slider_f = self.__elem[9]
            self.dmx_slider_f = self.__elem[10]
        self.property_changed_event.fire('dispersion_wobbler_f')

    @property
    def dispersion_wobbler_int_f(self):
        return self.__dispersion_wobbler_int

    @dispersion_wobbler_int_f.setter
    def dispersion_wobbler_int_f(self, value):
        self.__dispersion_wobbler_int = int(value)
        self.property_changed_event.fire('dispersion_wobbler_int_f')

    """
    FX
    """
    @property
    def fx_slider_f(self):
        return self.__elem[0]

    @fx_slider_f.setter
    def fx_slider_f(self, value):
        self.__elem[0] = value
        self.__eels_spec.locked_set_val(self.__elem[0], self.__names[0])
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")

    @property
    def fx_edit_f(self):
        return str(self.__elem[0])

    @fx_edit_f.setter
    def fx_edit_f(self, value):
        self.__elem[0] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[0], self.__names[0])
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")

    """
    FY
    """
    @property
    def fy_slider_f(self):
        return self.__elem[1]

    @fy_slider_f.setter
    def fy_slider_f(self, value):
        self.__elem[1] = value
        self.__eels_spec.locked_set_val(self.__elem[1], self.__names[1])
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")

    @property
    def fy_edit_f(self):
        return str(self.__elem[1])

    @fy_edit_f.setter
    def fy_edit_f(self, value):
        self.__elem[1] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[1], self.__names[1])
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")

    """
    SX
    """
    @property
    def sx_slider_f(self):
        return self.__elem[2]

    @sx_slider_f.setter
    def sx_slider_f(self, value):
        self.__elem[2] = value
        self.__eels_spec.locked_set_val(self.__elem[2], self.__names[2])
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")

    @property
    def sx_edit_f(self):
        return str(self.__elem[2])

    @sx_edit_f.setter
    def sx_edit_f(self, value):
        self.__elem[2] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[2], self.__names[2])
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")

    """
    SY
    """
    @property
    def sy_slider_f(self):
        return self.__elem[3]

    @sy_slider_f.setter
    def sy_slider_f(self, value):
        self.__elem[3] = value
        self.__eels_spec.locked_set_val(self.__elem[3], self.__names[3])
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")

    @property
    def sy_edit_f(self):
        return str(self.__elem[3])

    @sy_edit_f.setter
    def sy_edit_f(self, value):
        self.__elem[3] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[3], self.__names[3])
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")

    """
    DY
    """
    @property
    def dy_slider_f(self):
        return self.__elem[4]

    @dy_slider_f.setter
    def dy_slider_f(self, value):
        self.__elem[4] = value
        self.__eels_spec.locked_set_val(self.__elem[4], self.__names[4])
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")

    @property
    def dy_edit_f(self):
        return str(self.__elem[4])

    @dy_edit_f.setter
    def dy_edit_f(self, value):
        self.__elem[4] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[4], self.__names[4])
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")

    """
    TARE
    """

    @property
    def tare_edit_f(self):
        return self.__zlpTare

    @tare_edit_f.setter
    def tare_edit_f(self, value):
        try:
            self.__zlpTare = float(value)
        except:
            logging.info('***EELS SPEC***: ZLP tare must be float.')

    """
    Q1
    """
    @property
    def q1_slider_f(self):
        return self.__elem[5]

    @q1_slider_f.setter
    def q1_slider_f(self, value):
        self.__elem[5] = value
        self.__eels_spec.locked_set_val(self.__elem[5], self.__names[5])
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")

    @property
    def q1_edit_f(self):
        return str(self.__elem[5])

    @q1_edit_f.setter
    def q1_edit_f(self, value):
        sself.__elem[5] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[5], self.__names[5])
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")

    """
    Q2
    """
    @property
    def q2_slider_f(self):
        return self.__elem[6]

    @q2_slider_f.setter
    def q2_slider_f(self, value):
        self.__elem[6] = value
        self.__eels_spec.locked_set_val(self.__elem[6], self.__names[6])
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")

    @property
    def q2_edit_f(self):
        return str(self.__elem[6])

    @q2_edit_f.setter
    def q2_edit_f(self, value):
        self.__elem[6] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[6], self.__names[6])
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")

    """
    Q3
    """
    @property
    def q3_slider_f(self):
        return self.__elem[7]

    @q3_slider_f.setter
    def q3_slider_f(self, value):
        self.__elem[7] = value
        self.__eels_spec.locked_set_val(self.__elem[7], self.__names[7])
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")

    @property
    def q3_edit_f(self):
        return str(self.__elem[7])

    @q3_edit_f.setter
    def q3_edit_f(self, value):
        self.__elem[7] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[7], self.__names[7])
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")

    """
    Q4
    """
    @property
    def q4_slider_f(self):
        return self.__elem[8]

    @q4_slider_f.setter
    def q4_slider_f(self, value):
        self.__elem[8] = value
        self.__eels_spec.locked_set_val(self.__elem[8], self.__names[8])
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")

    @property
    def q4_edit_f(self):
        return str(self.__elem[8])

    @q4_edit_f.setter
    def q4_edit_f(self, value):
        self.__elem[8] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[8], self.__names[8])
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")

    """
    DX
    """
    @property
    def dx_slider_f(self):
        return self.__elem[9]

    @dx_slider_f.setter
    def dx_slider_f(self, value):
        self.__elem[9] = value
        self.__eels_spec.locked_set_val(self.__elem[9], self.__names[9])
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")

    @property
    def dx_edit_f(self):
        return str(self.__elem[9])

    @dx_edit_f.setter
    def dx_edit_f(self, value):
        self.__elem[9] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[9], self.__names[9])
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")

    """
    DMX
    """
    @property
    def dmx_slider_f(self):
        return self.__elem[10]

    @dmx_slider_f.setter
    def dmx_slider_f(self, value):
        self.__elem[10] = value
        self.__eels_spec.locked_set_val(self.__elem[10], self.__names[10])
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")

    @property
    def dmx_edit_f(self):
        return str(self.__elem[10])

    @dmx_edit_f.setter
    def dmx_edit_f(self, value):
        self.__elem[10] = int(value)
        self.__eels_spec.locked_set_val(self.__elem[10], self.__names[10])
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")

    """
    ENERGY OFFSET
    """
    @property
    def ene_offset_f(self):
        return int(self.__elem[11] * 4.095)

    @ene_offset_f.setter
    def ene_offset_f(self, value):
        self.__elem[11] = value / 4.095
        self.__eels_spec.locked_set_val(self.__elem[11], self.__names[11])
        self.property_changed_event.fire('ene_offset_f')
        self.property_changed_event.fire('ene_offset_edit_f')

    @property
    def ene_offset_edit_f(self):
        return self.__elem[11]

    @ene_offset_edit_f.setter
    def ene_offset_edit_f(self, value):
        self.__elem[11] = float(value)
        self.__eels_spec.locked_set_val(self.__elem[11], self.__names[11])
        self.property_changed_event.fire('ene_offset_f')
        self.property_changed_event.fire('ene_offset_edit_f')

    @property
    def vsm_wobbler_f(self):
        return self.__vsm_wobbler

    @vsm_wobbler_f.setter
    def vsm_wobbler_f(self, value):
        self.__vsm_wobbler = value
        if value:
            self.__eels_spec.wobbler_on(self.__elem[11], 30, self.__names[11])
        else:
            self.__eels_spec.wobbler_off()
            self.ene_offset_edit_f = self.__elem[11]