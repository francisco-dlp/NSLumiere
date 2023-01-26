# standard libraries
import gettext
import os
import json

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.swift.model import HardwareSource

from . import probe_inst

_ = gettext.gettext

class gainhandler:

    def __init__(self, instrument: probe_inst.probeDevice, event_loop):

        self.event_loop = event_loop
        self.instrument = instrument
        self.enabled = False
        self.property_changed_event_listener = self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener = self.instrument.busy_event.listen(self.prepare_widget_disable)

    def init_handler(self):
        self.ivg = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")
        self.instrument.init_handler()

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

    def save_lenses(self, widget):
        self.instrument.save_values()

    def probe_offset_reset_pb(self, widget):
        self.instrument.probe_offset0_f = 0
        self.instrument.probe_offset1_f = 0
        self.instrument.probe_offset2_f = 0
        self.instrument.probe_offset3_f = 0

    def adj_values(self, widget):
        if widget == self.obj_slider:
            self.obj_slider.maximum = self.obj_slider.value + 25000
            self.obj_slider.minimum = max(self.obj_slider.value - 25000, 0)
            self.full_range_obj.text = '(Fine)'

        if widget == self.c1_slider:
            self.c1_slider.maximum = self.c1_slider.value + 5000
            self.c1_slider.minimum = max(self.c1_slider.value - 5000, 0)
            self.full_range_c1.text = '(Fine)'

        if widget == self.c2_slider:
            self.c2_slider.maximum = self.c2_slider.value + 5000
            self.c2_slider.minimum = max(self.c2_slider.value - 5000, 0)
            self.full_range_c2.text = '(Fine)'

    def line_update(self, widget, text):
        if widget == self.obj_value:
            if text:
                value = int(float(text) * 1000000)
                self.obj_slider.maximum = value + 1000000
                self.obj_slider.minimum = max(value - 1000000, 0)
                self.full_range_obj.text = '(Coarse)'
        if widget == self.c1_value:
            if text:
                value = int(float(text) * 1000000)
                self.c1_slider.maximum = value + 500000
                self.c1_slider.minimum = max(value - 500000, 0)
                self.full_range_c1.text = '(Coarse)'
        if widget == self.c2_value:
            if text:
                value = int(float(text) * 1000000)
                self.c2_slider.maximum = value + 500000
                self.c2_slider.minimum = max(value - 500000, 0)
                self.full_range_c2.text = '(Coarse)'


class gainView:

    def __init__(self, instrument: probe_inst.probeDevice):
        ui = Declarative.DeclarativeUI()

        # fine adjustment label #
        self.full_range_obj = ui.create_label(name='full_range_obj', text='(Coarse)')
        self.full_range_c1 = ui.create_label(name='full_range_c1', text='(Coarse)')
        self.full_range_c2 = ui.create_label(name='full_range_c2', text='(Coarse)')

        ## wobbler ##
        self.wobbler_value = ui.create_line_edit(name='wobbler_value', width=150,
                                                 text='@binding(instrument.wobbler_intensity_f)')
        self.wobbler_slider_label = ui.create_label(name='wobbler_slider_label', text='Frequency [Hz]: ')
        self.wobbler_value_label = ui.create_label(name='wobbler_value_label',
                                                   text='@binding(instrument.wobbler_frequency_f)')
        self.wobbler_slider_frequency = ui.create_slider(name='wobbler_slider_frequency',
                                                         value='@binding(instrument.wobbler_frequency_f)', minimum=1,
                                                         maximum=10)
        self.wobbler_freq_row = ui.create_row(self.wobbler_slider_label, self.wobbler_value_label, ui.create_stretch())

        ### save ###

        self.save_pb = ui.create_push_button(text='Save Settings', name='save_pb', on_clicked="save_lenses")
        self.pb_row=ui.create_row(ui.create_stretch(), self.save_pb)

        ## objetive ##

        self.obj_cb = ui.create_check_box(text='Obj:', name='obj_label', checked='@binding(instrument.obj_global_f)')
        self.obj_value = ui.create_line_edit(name='obj_value', text='@binding(instrument.obj_edit_f)',
                                             on_text_edited='line_update')
        self.obj_row = ui.create_row(self.obj_cb, self.obj_value, self.full_range_obj, ui.create_stretch(), spacing=5)

        self.obj_slider = ui.create_slider(name='obj_slider', value='@binding(instrument.obj_slider_f)',
                                           minimum=1000000, maximum=9000000, on_slider_released='adj_values')

        self.obj_wobbler_cb = ui.create_check_box(text='Wobbler [Obj]: ', name='obj_wobbler_label',
                                                  checked='@binding(instrument.obj_wobbler_f)')



        self.obj_wobbler_row = ui.create_row(self.obj_wobbler_cb, self.wobbler_value)

        self.astig0_label=ui.create_label(name='astig0_label', text='Astig 00: ')
        self.astig0_label_value = ui.create_label(name='astig0_label_value', text='@binding(instrument.obj_stigmateur0_f)')
        self.astig0_row = ui.create_row(self.astig0_label, self.astig0_label_value, ui.create_stretch())
        self.astig0_slider=ui.create_slider(name='astig0_slider', value='@binding(instrument.obj_stigmateur0_f)', minimum=-1000, maximum=1000)
        self.astig1_label=ui.create_label(name='astig1_label', text='Astig 01: ')
        self.astig1_label_value = ui.create_label(name='astig1_label_value', text='@binding(instrument.obj_stigmateur1_f)')
        self.astig1_row = ui.create_row(self.astig1_label, self.astig1_label_value, ui.create_stretch())
        self.astig1_slider=ui.create_slider(name='astig1_slider', value='@binding(instrument.obj_stigmateur1_f)', minimum=-1000, maximum=1000)
        self.astig_column=ui.create_column(self.astig0_row, self.astig0_slider, self.astig1_row, self.astig1_slider)

        self.astig_group=ui.create_group(title='Objective Astigmators', content=self.astig_column)

        self.probe_offset0_label = ui.create_label(name='probe_offset0_label', text='Probe offset 0: ')
        self.probe_offset0_value_label = ui.create_label(name='probe_offset0_value_label', text='@binding(instrument.probe_offset0_f)')
        self.probe_offset0_row = ui.create_row(self.probe_offset0_label, self.probe_offset0_value_label, ui.create_stretch())
        self.probe_offset0_slider = ui.create_slider(name='probe_offset0_slider', value='@binding(instrument.probe_offset0_f)',
                                              minimum=-280000, maximum=280000)

        self.probe_offset1_label = ui.create_label(name='probe_offset1_label', text='Probe offset 1: ')
        self.probe_offset1_value_label = ui.create_label(name='probe_offset1_value_label',
                                                         text='@binding(instrument.probe_offset1_f)')
        self.probe_offset1_row = ui.create_row(self.probe_offset1_label, self.probe_offset1_value_label,
                                               ui.create_stretch())
        self.probe_offset1_slider = ui.create_slider(name='probe_offset1_slider',
                                                     value='@binding(instrument.probe_offset1_f)',
                                                     minimum=-280000, maximum=280000)

        self.probe_offset2_label = ui.create_label(name='probe_offset2_label', text='Probe offset 2: ')
        self.probe_offset2_value_label = ui.create_label(name='probe_offset2_value_label',
                                                         text='@binding(instrument.probe_offset2_f)')
        self.probe_offset2_row = ui.create_row(self.probe_offset2_label, self.probe_offset2_value_label,
                                               ui.create_stretch())
        self.probe_offset2_slider = ui.create_slider(name='probe_offset2_slider',
                                                     value='@binding(instrument.probe_offset2_f)',
                                                     minimum=-280000, maximum=280000)

        self.probe_offset3_label = ui.create_label(name='probe_offset3_label', text='Probe offset 3: ')
        self.probe_offset3_value_label = ui.create_label(name='probe_offset3_value_label',
                                                         text='@binding(instrument.probe_offset3_f)')
        self.probe_offset3_row = ui.create_row(self.probe_offset3_label, self.probe_offset3_value_label,
                                               ui.create_stretch())
        self.probe_offset3_slider = ui.create_slider(name='probe_offset3_slider',
                                                     value='@binding(instrument.probe_offset3_f)',
                                                     minimum=-280000, maximum=280000)
        self.probe_offset_reset = ui.create_push_button(text='Reset', name='probe_offset_reset', width = 100, on_clicked="probe_offset_reset_pb")



        self.probe_offset_column = ui.create_column(self.probe_offset0_row, self.probe_offset0_slider,
                                                    self.probe_offset1_row, self.probe_offset1_slider,
                                                    self.probe_offset2_row, self.probe_offset2_slider,
                                                    self.probe_offset3_row, self.probe_offset3_slider,
                                                    self.probe_offset_reset)

        self.probe_offset_group = ui.create_group(title='Probe Offset', content=self.probe_offset_column)


        self.objective_tab = ui.create_tab(label='Objective',
                                           content=ui.create_column(self.obj_row,
                                                                    self.obj_slider, self.obj_wobbler_row,
                                                                    self.wobbler_freq_row,
                                                                    self.wobbler_slider_frequency,
                                                                    self.astig_group,
                                                                    self.probe_offset_group,
                                                                    self.pb_row))

        ## condensers ##

        self.c1_cb = ui.create_check_box(text='C1:', name='c1_label', checked='@binding(instrument.c1_global_f)')
        self.c1_value = ui.create_line_edit(name='c1_value', text='@binding(instrument.c1_edit_f)',
                                            on_text_edited='line_update')
        self.c1_row = ui.create_row(self.c1_cb, self.c1_value, self.full_range_c1, ui.create_stretch(), spacing=5)

        self.c1_slider = ui.create_slider(name='c1_slider', value='@binding(instrument.c1_slider_f)', maximum=1000000,
                                          on_slider_released='adj_values')

        self.c1_wobbler_cb = ui.create_check_box(text='Wobbler [C1]: ', name='c1_wobbler_label',
                                                 checked='@binding(instrument.c1_wobbler_f)')
        self.c1_wobbler_row = ui.create_row(self.c1_wobbler_cb, self.wobbler_value)

        self.c2_cb = ui.create_check_box(text='C2:', name='c2_label', checked='@binding(instrument.c2_global_f)')
        self.c2_value = ui.create_line_edit(name='c2_value', text='@binding(instrument.c2_edit_f)',
                                            on_text_edited='line_update')
        self.c2_row = ui.create_row(self.c2_cb, self.c2_value, self.full_range_c2, ui.create_stretch(), spacing=5)

        self.c2_slider = ui.create_slider(name='c2_slider', value='@binding(instrument.c2_slider_f)', maximum=1000000,
                                          on_slider_released='adj_values')

        self.c2_wobbler_cb = ui.create_check_box(text='Wobbler [C2]: ', name='c2_wobbler_label',
                                                 checked='@binding(instrument.c2_wobbler_f)')
        self.c2_wobbler_row = ui.create_row(self.c2_wobbler_cb, self.wobbler_value)


        self.astig2_label=ui.create_label(name='astig1_labe2', text='Astig 02: ')
        self.astig2_label_value = ui.create_label(name='astig2_label_value',
                                                  text='@binding(instrument.gun_stigmateur0_f)')
        self.astig2_row = ui.create_row(self.astig2_label, self.astig2_label_value, ui.create_stretch())
        self.astig2_slider=ui.create_slider(name='astig2_slider', value='@binding(instrument.gun_stigmateur0_f)', minimum=-1000, maximum=1000)

        self.astig3_label=ui.create_label(name='astig3_label', text='Astig 03: ')
        self.astig3_label_value = ui.create_label(name='astig3_label_value',
                                                  text='@binding(instrument.gun_stigmateur1_f)')
        self.astig3_row = ui.create_row(self.astig3_label, self.astig3_label_value, ui.create_stretch())
        self.astig3_slider=ui.create_slider(name='astig3_slider', value='@binding(instrument.gun_stigmateur1_f)', minimum=-1000, maximum=1000)

        self.cond_astig_column=ui.create_column(self.astig2_row, self.astig2_slider, self.astig3_row, self.astig3_slider)

        self.cond_astig_group=ui.create_group(title='Condenser Astigmators', content=self.cond_astig_column)



        self.condenser_tab = ui.create_tab(label='Condenser',
                                           content=ui.create_column(self.c1_row, self.c1_slider,
                                                                    self.c1_wobbler_row, self.wobbler_freq_row,
                                                                    self.c2_row, self.c2_slider,
                                                                    self.c2_wobbler_row, self.wobbler_freq_row,
                                                                    self.cond_astig_group,
                                                                    self.pb_row))

        self.tabs = ui.create_tabs(self.objective_tab, self.condenser_tab)

        self.ui_view = ui.create_column(self.tabs)

def create_spectro_panel(document_controller, panel_id, properties):
    instrument = properties["instrument"]
    ui_handler = gainhandler(instrument, document_controller.event_loop)
    ui_view = gainView(instrument)
    panel = Panel.Panel(document_controller, panel_id, properties)

    finishes = list()
    panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)

    for finish in finishes:
        finish()
    if ui_handler and hasattr(ui_handler, "init_handler"):
        ui_handler.init_handler()
    return panel

def run(instrument: probe_inst.probeDevice) -> None:
    panel_id = "Probe"  # make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Probe")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
