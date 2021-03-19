# standard libraries
import json
import os
import logging
import time

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), "global_settings.json"))
with open(abs_path) as savfile:
    settings = json.load(savfile)
DEBUG = settings["EELS"]["DEBUG"]


if DEBUG:
    from . import eels_spec_vi as spec
else:
    from . import eels_spec as spec


class EELS_SPEC_Device(Observable.Observable):

    def __init__(self):
        self.property_changed_event = Event.Event()
        self.property_changed_power_event = Event.Event()
        self.communicating_event = Event.Event()
        self.busy_event = Event.Event()

        self.__sendmessage = spec.SENDMYMESSAGEFUNC(self.sendMessageFactory())
        self.__eels_spec = spec.espec(self.__sendmessage)

        self.__fx = 0
        self.__fy = 0
        self.__sx = 0
        self.__sy = 0
        self.__dy = 0
        self.__q1 = 0
        self.__q2 = 0
        self.__q3 = 0
        self.__q4 = 0
        self.__dx = 0
        self.__dmx = 0
        self.ene_offset_f=0

        self.__focus_wobbler_int=25
        self.__dispersion_wobbler_int=25
        self.__focus_wobbler_index = 0
        self.__dispersion_wobbler_index = 0


        self.__EHT = '3'

        try:
            inst_dir = os.path.dirname(__file__)
            abs_path = os.path.join(inst_dir, 'eels_settings.json')
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

    def set_spec_values(self, value):
        inst_dir = os.path.dirname(__file__)
        abs_path = os.path.join(inst_dir, 'eels_settings.json')
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

    def sendMessageFactory(self):
        def sendMessage(message):
            if message == 1:
                logging.info("***EELS SPECTROMETER***: Could not find EELS Spec. Check Hardware")
            if message == 2:
                logging.info(
                    "***EELS SPECTROMETER***: Problem communicating over serial port. Easy check using Serial Port Monitor.")
            if message == 3:
                logging.info("***EELS SPECTROMETER***: Attempt to write a value out of range.")

        return sendMessage

    ### General ###

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
        self.__dispIndex = value
        self.set_spec_values(str(value))
        self.property_changed_event.fire('disp_change_f')

    ### WOBBLER ###

    @property
    def focus_wobbler_f(self):
        return self.__focus_wobbler_index

    @focus_wobbler_f.setter
    def focus_wobbler_f(self, value):
        focus_list = ['OFF', 'FX', 'FY', 'SX', 'SY', 'DY']
        focus_list_values=[0, self.__fx, self.__fy, self.__sx, self.__sy, self.__dy]
        self.__focus_wobbler_index = value
        if value:
            self.__eels_spec.wobbler_on(focus_list_values[value], self.__focus_wobbler_int, focus_list[value])
        else:
            try:
                self.__eels_spec.wobbler_off()
                time.sleep(1.1)
                self.fx_slider_f=self.__fx
                self.fy_slider_f = self.__fy
                self.sx_slider_f = self.__sx
                self.sy_slider_f = self.__sy
                self.dy_slider_f = self.__dy
            except:
                logging.info('***EELS SPECTROMETER***: Wobbler is OFF.')
        self.property_changed_event.fire('focus_wobbler_f')

    @property
    def focus_wobbler_int_f(self):
        return self.__focus_wobbler_int

    @focus_wobbler_int_f.setter
    def focus_wobbler_int_f(self, value):
        self.__focus_wobbler_int = int(value)
        if self.__focus_wobbler_index:
            temp=self.focus_wobbler_f
            self.focus_wobbler_f=0
            self.focus_wobbler_f=temp
        self.property_changed_event.fire('focus_wobbler_int_f')

    @property
    def dispersion_wobbler_f(self):
        return self.__dispersion_wobbler_index

    @dispersion_wobbler_f.setter
    def dispersion_wobbler_f(self, value):
        disp_list = ['OFF', 'Q1', 'Q2', 'Q3', 'Q4', 'DX', 'DMX']
        disp_list_values = [0, self.__q1, self.__q2, self.__q3, self.__q4, self.__dx, self.__dmx]
        self.__dispersion_wobbler_index = value
        if value:
            self.__eels_spec.wobbler_on(disp_list_values[value], self.__dispersion_wobbler_int, disp_list[value])
        else:
            try:
                self.__eels_spec.wobbler_off()
                time.sleep(1.1)
                self.q1_slider_f=self.__q1
                self.q2_slider_f = self.__q2
                self.q3_slider_f = self.__q3
                self.q4_slider_f = self.__q4
                self.dx_slider_f = self.__dx
                self.dmx_slider_f = self.__dmx
            except:
                logging.info('***EELS SPECTROMETER***: Wobbler is OFF.')
        self.property_changed_event.fire('dispersion_wobbler_f')

    @property
    def dispersion_wobbler_int_f(self):
        return self.__dispersion_wobbler_int

    @dispersion_wobbler_int_f.setter
    def dispersion_wobbler_int_f(self, value):
        self.__dispersion_wobbler_int = int(value)
        if self.__dispersion_wobbler_index:
            temp=self.dispersion_wobbler_f
            self.dispersion_wobbler_f=0
            self.dispersion_wobbler_f=temp
        self.property_changed_event.fire('dispersion_wobbler_int_f')


    ### FX ###
    @property
    def fx_slider_f(self):
        return self.__fx

    @fx_slider_f.setter
    def fx_slider_f(self, value):
        self.__fx = value
        self.__eels_spec.set_val(self.__fx, 'FX')
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")

    @property
    def fx_edit_f(self):
        return str(self.__fx)

    @fx_edit_f.setter
    def fx_edit_f(self, value):
        self.__fx = int(value)
        self.__eels_spec.set_val(self.__fx, 'FX')
        self.property_changed_event.fire("fx_slider_f")
        self.property_changed_event.fire("fx_edit_f")

    ### FY ###
    @property
    def fy_slider_f(self):
        return self.__fy

    @fy_slider_f.setter
    def fy_slider_f(self, value):
        self.__fy = value
        self.__eels_spec.set_val(self.__fy, 'FY')
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")

    @property
    def fy_edit_f(self):
        return str(self.__fy)

    @fy_edit_f.setter
    def fy_edit_f(self, value):
        self.__fy = int(value)
        self.__eels_spec.set_val(self.__fy, 'FY')
        self.property_changed_event.fire("fy_slider_f")
        self.property_changed_event.fire("fy_edit_f")

    ### SX ###
    @property
    def sx_slider_f(self):
        return self.__sx

    @sx_slider_f.setter
    def sx_slider_f(self, value):
        self.__sx = value
        self.__eels_spec.set_val(self.__sx, 'SX')
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")

    @property
    def sx_edit_f(self):
        return str(self.__sx)

    @sx_edit_f.setter
    def sx_edit_f(self, value):
        self.__sx = int(value)
        self.__eels_spec.set_val(self.__sx, 'SX')
        self.property_changed_event.fire("sx_slider_f")
        self.property_changed_event.fire("sx_edit_f")

    ### SY ###
    @property
    def sy_slider_f(self):
        return self.__sy

    @sy_slider_f.setter
    def sy_slider_f(self, value):
        self.__sy = value
        self.__eels_spec.set_val(self.__sy, 'SY')
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")

    @property
    def sy_edit_f(self):
        return str(self.__sy)

    @sy_edit_f.setter
    def sy_edit_f(self, value):
        self.__sy = int(value)
        self.__eels_spec.set_val(self.__sy, 'SY')
        self.property_changed_event.fire("sy_slider_f")
        self.property_changed_event.fire("sy_edit_f")

    ### DY ###
    @property
    def dy_slider_f(self):
        return self.__dy

    @dy_slider_f.setter
    def dy_slider_f(self, value):
        self.__dy = value
        self.__eels_spec.set_val(self.__dy, 'DY')
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")

    @property
    def dy_edit_f(self):
        return str(self.__dy)

    @dy_edit_f.setter
    def dy_edit_f(self, value):
        self.__dy = int(value)
        self.__eels_spec.set_val(self.__dy, 'DY')
        self.property_changed_event.fire("dy_slider_f")
        self.property_changed_event.fire("dy_edit_f")

    ### Q1 ###
    @property
    def q1_slider_f(self):
        return self.__q1

    @q1_slider_f.setter
    def q1_slider_f(self, value):
        self.__q1 = value
        self.__eels_spec.set_val(self.__q1, 'Q1')
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")

    @property
    def q1_edit_f(self):
        return str(self.__q1)

    @q1_edit_f.setter
    def q1_edit_f(self, value):
        self.__q1 = int(value)
        self.__eels_spec.set_val(self.__q1, 'Q1')
        self.property_changed_event.fire("q1_slider_f")
        self.property_changed_event.fire("q1_edit_f")

    ### Q2 ###
    @property
    def q2_slider_f(self):
        return self.__q2

    @q2_slider_f.setter
    def q2_slider_f(self, value):
        self.__q2 = value
        self.__eels_spec.set_val(self.__q2, 'Q2')
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")

    @property
    def q2_edit_f(self):
        return str(self.__q2)

    @q2_edit_f.setter
    def q2_edit_f(self, value):
        self.__q2 = int(value)
        self.__eels_spec.set_val(self.__q2, 'Q2')
        self.property_changed_event.fire("q2_slider_f")
        self.property_changed_event.fire("q2_edit_f")

    ### Q3 ###
    @property
    def q3_slider_f(self):
        return self.__q3

    @q3_slider_f.setter
    def q3_slider_f(self, value):
        self.__q3 = value
        self.__eels_spec.set_val(self.__q3, 'Q3')
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")

    @property
    def q3_edit_f(self):
        return str(self.__q3)

    @q3_edit_f.setter
    def q3_edit_f(self, value):
        self.__q3 = int(value)
        self.__eels_spec.set_val(self.__q3, 'Q3')
        self.property_changed_event.fire("q3_slider_f")
        self.property_changed_event.fire("q3_edit_f")

    ### Q4 ###
    @property
    def q4_slider_f(self):
        return self.__q4

    @q4_slider_f.setter
    def q4_slider_f(self, value):
        self.__q4 = value
        self.__eels_spec.set_val(self.__q4, 'Q4')
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")

    @property
    def q4_edit_f(self):
        return str(self.__q4)

    @q4_edit_f.setter
    def q4_edit_f(self, value):
        self.__q4 = int(value)
        self.__eels_spec.set_val(self.__q4, 'Q4')
        self.property_changed_event.fire("q4_slider_f")
        self.property_changed_event.fire("q4_edit_f")

    ### DX ###
    @property
    def dx_slider_f(self):
        return self.__dx

    @dx_slider_f.setter
    def dx_slider_f(self, value):
        self.__dx = value
        self.__eels_spec.set_val(self.__dx, 'DX')
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")

    @property
    def dx_edit_f(self):
        return str(self.__dx)

    @dx_edit_f.setter
    def dx_edit_f(self, value):
        self.__dx = int(value)
        self.__eels_spec.set_val(self.__dx, 'DX')
        self.property_changed_event.fire("dx_slider_f")
        self.property_changed_event.fire("dx_edit_f")

    ### DMX ###
    @property
    def dmx_slider_f(self):
        return self.__dmx

    @dmx_slider_f.setter
    def dmx_slider_f(self, value):
        self.__dmx = value
        self.__eels_spec.set_val(self.__dmx, 'AL')
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")

    @property
    def dmx_edit_f(self):
        return str(self.__dmx)

    @dmx_edit_f.setter
    def dmx_edit_f(self, value):
        self.__dmx = int(value)
        self.__eels_spec.set_val(self.__dmx, 'AL')
        self.property_changed_event.fire("dmx_slider_f")
        self.property_changed_event.fire("dmx_edit_f")

    @property
    def ene_offset_f(self):
        return int(self.__ene_offset*1000.)

    @ene_offset_f.setter
    def ene_offset_f(self, value):
        self.__ene_offset = value/1000.
        self.__eels_spec.set_vsm(self.__ene_offset)
        self.property_changed_event.fire('ene_offset_f')
        self.property_changed_event.fire('ene_offset_edit_f')

    @property
    def ene_offset_edit_f(self):
        return self.__ene_offset

    @ene_offset_edit_f.setter
    def ene_offset_edit_f(self, value):
        self.__ene_offset = float(value)
        self.__eels_spec.set_vsm(self.__ene_offset)
        self.property_changed_event.fire('ene_offset_f')
        self.property_changed_event.fire('ene_offset_edit_f')