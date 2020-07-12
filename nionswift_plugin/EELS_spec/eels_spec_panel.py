# standard libraries
import gettext
import os
import json

# local libraries
from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Widgets
from nion.utils import Binding
from nion.utils import Converter
from nion.utils import Geometry
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.swift.model import HardwareSource
import threading

from . import eels_spec_inst

import logging

_ = gettext.gettext
from nion.utils import Model

import inspect


class eels_spec_handler:

    def __init__(self, instrument: eels_spec_inst.EELS_SPEC_Device, event_loop):

        self.event_loop = event_loop
        self.instrument = instrument
        self.enabled = False
        self.property_changed_event_listener = self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener = self.instrument.busy_event.listen(self.prepare_widget_disable)

        self.ivg = None

    async def do_enable(self, enabled=True, not_affected_widget_name_list=None):
        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self, var), UserInterface.Widget):
                    widg = getattr(self, var)
                    setattr(widg, "enabled", enabled)

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, []))

    def prepare_widget_disable(self, value):
        self.event_loop.create_task(self.do_enable(False, []))

    def save_spec(self, widget):
        if not self.ivg:
            self.ivg = HardwareSource.HardwareSourceManager().get_instrument_by_id("Instrument_VG")

        panel_dir = os.path.dirname(__file__)
        abs_path = os.path.join(panel_dir, 'eels_settings.json')
        with open(abs_path) as savfile:
            json_object = json.load(savfile)

        json_object[str(self.ivg.EHT_f)][self.dispersion_value.current_index] = { \
            'range': self.range_value.text, 'note': self.note_text.text, 'fx': self.fx_value.text, 'fy': self.fy_value.text,
            'sx': self.sx_value.text,
            'sy': self.sy_value.text, 'dy': self.dy_value.text, 'q1': self.q1_value.text, \
            'q2': self.q2_value.text, 'q3': self.q3_value.text, 'q4': self.q4_value.text, \
            'dx': self.dx_value.text, 'dmx': self.dmx_value.text, }

        json_object[str(self.ivg.EHT_f)]['last'] = self.dispersion_value.current_index

        with open(abs_path, 'w') as json_file:
            json.dump(json_object, json_file, indent=4)

        self.full_range(widget)

    def full_range(self, widget):

        self.fx_slider.maximum = 32767
        self.fx_slider.minimum = -32767

        self.fy_slider.maximum = 32767
        self.fy_slider.minimum = -32767

        self.sx_slider.maximum = 32767
        self.sx_slider.minimum = -32767

        self.sy_slider.maximum = 32767
        self.sy_slider.minimum = -32767

        self.dy_slider.maximum = 32767
        self.dy_slider.minimum = -32767

        self.q1_slider.maximum = 32767
        self.q1_slider.minimum = -32767

        self.q2_slider.maximum = 32767
        self.q2_slider.minimum = -32767

        self.q3_slider.maximum = 32767
        self.q3_slider.minimum = -32767

        self.q4_slider.maximum = 32767
        self.q4_slider.minimum = -32767

        self.dx_slider.maximum = 32767
        self.dx_slider.minimum = -32767

        self.dmx_slider.maximum = 32767
        self.dmx_slider.minimum = -32767

    def slider_release(self, widget):
        widget.maximum = widget.value + 2500
        widget.minimum = widget.value - 2500


class eels_spec_View:

    def __init__(self, instrument: eels_spec_inst.EELS_SPEC_Device):
        ui = Declarative.DeclarativeUI()

        # Note
        self.note_label=ui.create_label(text='Note: ', name='note_label')
        self.note_text = ui.create_line_edit(name='note_text', text='@binding(instrument.note_f)')
        self.note_row = ui.create_row(self.note_label, self.note_text)

        # full_range

        self.full_range_pb = ui.create_push_button(name='full_range_pb', text='Full Range', on_clicked='full_range')

        # range selection

        self.dispersion_label = ui.create_label(text='Dispersion: ')
        self.dispersion_value = ui.create_combo_box(name='dispersion_value', items=['d1', 'd2', 'd3'],
                                                    current_index='@binding(instrument.disp_change_f)')

        self.range_label = ui.create_label(text='Dispersion: ')
        self.range_value = ui.create_line_edit(name='range_value', text='@binding(instrument.range_f)')

        # first order

        self.fx_label = ui.create_label(text='FX: ', name='fx_label')
        self.fx_value = ui.create_line_edit(name='fx_value', text='@binding(instrument.fx_' + 'edit_f)')
        self.fx_row = ui.create_row(self.fx_label, self.fx_value)
        self.fx_slider = ui.create_slider(name='fx_slider', value='@binding(instrument.fx_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.fy_label = ui.create_label(text='FY: ', name='fy_label')
        self.fy_value = ui.create_line_edit(name='fy_value', text='@binding(instrument.fy_edit_f)')
        self.fy_row = ui.create_row(self.fy_label, self.fy_value)
        self.fy_slider = ui.create_slider(name='fy_slider', value='@binding(instrument.fy_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.first_order_group = ui.create_group(title='1st Order', content=ui.create_column( \
            self.fx_row, self.fx_slider, ui.create_spacing(10), \
            self.fy_row, self.fy_slider))

        # sec order

        self.sx_label = ui.create_label(text='SX: ', name='sx_label')
        self.sx_value = ui.create_line_edit(name='sx_value', text='@binding(instrument.sx_edit_f)')
        self.sx_row = ui.create_row(self.sx_label, self.sx_value)
        self.sx_slider = ui.create_slider(name='sx_slider', value='@binding(instrument.sx_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.sy_label = ui.create_label(text='SY: ', name='sy_label')
        self.sy_value = ui.create_line_edit(name='sy_value', text='@binding(instrument.sy_edit_f)')
        self.sy_row = ui.create_row(self.sy_label, self.sy_value)
        self.sy_slider = ui.create_slider(name='sy_slider', value='@binding(instrument.sy_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.dy_label = ui.create_label(text='DY: ', name='dy_label')
        self.dy_value = ui.create_line_edit(name='dy_value', text='@binding(instrument.dy_edit_f)')
        self.dy_row = ui.create_row(self.dy_label, self.dy_value)
        self.dy_slider = ui.create_slider(name='dy_slider', value='@binding(instrument.dy_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.second_order_group = ui.create_group(title='2nd Order', content=ui.create_column( \
            self.sx_row, self.sx_slider, ui.create_spacing(10), \
            self.sy_row, self.sy_slider, ui.create_spacing(10), \
            self.dy_row, self.dy_slider))

        #wobbler funcs
        self.wobbler_combo=ui.create_combo_box(name='wobbler_combo', items=['OFF', 'Fx', 'Fy', 'Sx', 'Sy', 'Dy'], current_index='@binding(instrument.focus_wobbler_f)')
        self.wobbler_int=ui.create_line_edit(name='wobbler_int', width=50, text='@binding(instrument.focus_wobbler_int_f)')
        self.wobbler_row=ui.create_row(self.wobbler_combo, ui.create_spacing(10), self.wobbler_int, ui.create_stretch())
        self.wobbler_group = ui.create_group(title='Wobbler', content=self.wobbler_row)

        # save button

        self.save_pb = ui.create_push_button(text='Save Settings', name='save_pb', on_clicked='save_spec', width='100')
        self.pb_row = ui.create_row(self.full_range_pb, ui.create_stretch(), self.save_pb)

        # first tab

        self.focus_tab = ui.create_tab(label='Focus', content=ui.create_column( \
            self.dispersion_label, self.dispersion_value, ui.create_stretch(), \
            self.note_row, ui.create_stretch(), \
            self.range_label, self.range_value, ui.create_stretch(), \
            self.first_order_group, ui.create_stretch(), \
            self.second_order_group, \
            self.wobbler_group, \
            self.pb_row))

        # begin second tab

        self.q1_label = ui.create_label(text='Q1: ', name='q1_label')
        self.q1_value = ui.create_line_edit(name='q1_value', text='@binding(instrument.q1_edit_f)')
        self.q1_row = ui.create_row(self.q1_label, self.q1_value)
        self.q1_slider = ui.create_slider(name='q1_slider', value='@binding(instrument.q1_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.q2_label = ui.create_label(text='Q2: ', name='q2_label')
        self.q2_value = ui.create_line_edit(name='q2_value', text='@binding(instrument.q2_edit_f)')
        self.q2_row = ui.create_row(self.q2_label, self.q2_value)
        self.q2_slider = ui.create_slider(name='q2_slider', value='@binding(instrument.q2_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.q3_label = ui.create_label(text='Q3: ', name='q3_label')
        self.q3_value = ui.create_line_edit(name='q3_value', text='@binding(instrument.q3_edit_f)')
        self.q3_row = ui.create_row(self.q3_label, self.q3_value)
        self.q3_slider = ui.create_slider(name='q3_slider', value='@binding(instrument.q3_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.q4_label = ui.create_label(text='Q4: ', name='q4_label')
        self.q4_value = ui.create_line_edit(name='q4_value', text='@binding(instrument.q4_edit_f)')
        self.q4_row = ui.create_row(self.q4_label, self.q4_value)
        self.q4_slider = ui.create_slider(name='q4_slider', value='@binding(instrument.q4_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.dx_label = ui.create_label(text='DX: ', name='dx_label')
        self.dx_value = ui.create_line_edit(name='dx_value', text='@binding(instrument.dx_edit_f)')
        self.dx_row = ui.create_row(self.dx_label, self.dx_value)
        self.dx_slider = ui.create_slider(name='dx_slider', value='@binding(instrument.dx_slider_f)', minimum=-32767,
                                          maximum=32767, on_slider_released='slider_release')

        self.dmx_label = ui.create_label(text='DMX: ', name='dmx_label')
        self.dmx_value = ui.create_line_edit(name='dmx_value', text='@binding(instrument.dmx_edit_f)')
        self.dmx_row = ui.create_row(self.dmx_label, self.dmx_value)
        self.dmx_slider = ui.create_slider(name='dmx_slider', value='@binding(instrument.dmx_slider_f)', minimum=-32767,
                                           maximum=32767, on_slider_released='slider_release')

        # wobbler funcs second tab
        self.wobbler_combo_02 = ui.create_combo_box(name='wobbler_combo', items=['OFF', 'Q1', 'Q2', 'Q3', 'Q4', 'Dx', 'DMx'], current_index='@binding(instrument.dispersion_wobbler_f)')
        self.wobbler_int_02 = ui.create_line_edit(name='wobbler_int', width=50, text='@binding(instrument.dispersion_wobbler_int_f)')
        self.wobbler_row_02 = ui.create_row(self.wobbler_combo_02, ui.create_spacing(10), self.wobbler_int_02,
                                         ui.create_stretch())
        self.wobbler_group_02 = ui.create_group(title='Wobbler', content=self.wobbler_row_02)

        # second tab

        self.dispersion_tab = ui.create_tab(label='Dispersion', content=ui.create_column( \
            self.q1_row, self.q1_slider, \
            self.q2_row, self.q2_slider, \
            self.q3_row, self.q3_slider, \
            self.q4_row, self.q4_slider, \
            self.dx_row, self.dx_slider, \
            self.dmx_row, self.dmx_slider, \
            self.wobbler_group_02, \
            self.pb_row))

        # third tab

        self.vsm_label = ui.create_label(text='Energy Offset: ')
        self.vsm_value = ui.create_line_edit(name='vsm_value', text='@binding(instrument.ene_offset_edit_f)')
        self.vsm_row=ui.create_row(self.vsm_label, self.vsm_value)
        self.vsm_slider=ui.create_slider(name='vsm_slider', value='@binding(instrument.ene_offset_f)', minimum=-1000, maximum=1000)
        self.vsm_tab = ui.create_tab(label='VSM', content=ui.create_column( \
            self.vsm_row, self.vsm_slider, ui.create_stretch()))

        # all tabs

        self.tabs = ui.create_tabs(self.focus_tab, self.dispersion_tab, self.vsm_tab)

        # create ui view

        self.ui_view = ui.create_column(self.tabs)


def create_spectro_panel(document_controller, panel_id, properties):
    instrument = properties["instrument"]
    ui_handler = eels_spec_handler(instrument, document_controller.event_loop)
    ui_view = eels_spec_View(instrument)
    panel = Panel.Panel(document_controller, panel_id, properties)

    finishes = list()
    panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)

    for finish in finishes:
        finish()
    if ui_handler and hasattr(ui_handler, "init_handler"):
        ui_handler.init_handler()
    return panel


def run(instrument: eels_spec_inst.EELS_SPEC_Device) -> None:
    panel_id = "EELS Spectrometer"  # make sure it is unique, otherwise only one of the panel will be displayed
    name = _("EELS Spectrometer")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
