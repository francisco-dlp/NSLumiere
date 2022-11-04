# standard libraries
import gettext
import os
import json

# local libraries
from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface
from . import diaf_inst

_ = gettext.gettext


class diafhandler:

    def __init__(self, instrument: diaf_inst.diafDevice, event_loop):

        self.event_loop = event_loop
        self.instrument = instrument
        self.enabled = False
        self.property_changed_event_listener = self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener = self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.set_full_range_listener = self.instrument.set_full_range.listen(self.total_range_2)

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

    def save_ROA(self, widget):
        self.instrument.save_values(self.obj_combo_box.current_item, 'ROA')
        self.total_range(widget)

    def save_SA(self, widget):
        self.instrument.save_values(self.sa_combo_box.current_item, 'VOA')
        self.total_range(widget)

    def total_range_2(self):
        self.m1_slider.maximum = 1300000
        self.m1_slider.minimum = 50000

        self.m2_slider.maximum = 95000
        self.m2_slider.minimum = 80000

        self.m3_slider.maximum = 130000
        self.m3_slider.minimum = 50000

        self.m4_slider.maximum = 50000
        self.m4_slider.minimum = 65000

        self.m1_range.text = '(Coarse)'
        self.m2_range.text = '(Coarse)'
        self.m3_range.text = '(Coarse)'
        self.m4_range.text = '(Coarse)'

    def total_range(self, widget):
        self.total_range_2()

    def slider_release(self, widget):
        widget.maximum = widget.value + 2000
        widget.minimum = widget.value - 2000
        if widget==self.m1_slider: self.m1_range.text = '(Fine)'
        elif widget==self.m2_slider: self.m2_range.text = '(Fine)'
        elif widget==self.m3_slider: self.m3_range.text = '(Fine)'
        elif widget==self.m4_slider: self.m4_range.text = '(Fine)'


class diafView:

    def __init__(self, instrument: diaf_inst.diafDevice):
        ui = Declarative.DeclarativeUI()

        self.m1_range = ui.create_label(name='m1_range', text='(Coarse)')
        self.m2_range = ui.create_label(name='m2_range', text='(Coarse)')
        self.m3_range = ui.create_label(name='m3_range', text='(Coarse)')
        self.m4_range = ui.create_label(name='m4_range', text='(Coarse)')

        self.full_range_pb = ui.create_push_button(name='full_range_pb', text='Full Range', on_clicked='total_range',
                                                   width=150)
        self.save_obj_pb = ui.create_push_button(name='save_obj_pb', text='Save Settings', on_clicked='save_ROA',
                                                 width=150)
        self.save_sa_pb = ui.create_push_button(name='save_sa_pb', text='Save Settings', on_clicked='save_SA',
                                                width=150)

        self.obj_combo_box = ui.create_combo_box(name='obj_combo_box', items=['None', '50', '100', '150'],
                                                 current_index='@binding(instrument.roa_change_f)')
        self.m1_slider_label = ui.create_label(name='m1_slider_label', text='@binding(instrument.m1_f)')
        self.m1_slider_labels = ui.create_row(self.m1_slider_label, self.m1_range, ui.create_stretch(), spacing=12)
        self.m1_slider = ui.create_slider(name='m1_slider', value='@binding(instrument.m1_f)', minimum=40000,
                                          maximum=130000, on_slider_released='slider_release')
        self.m2_slider_label = ui.create_label(name='m2_slider_label', text='@binding(instrument.m2_f)')
        self.m2_slider_labels = ui.create_row(self.m2_slider_label, self.m2_range, ui.create_stretch(), spacing=12)
        self.m2_slider = ui.create_slider(name='m2_slider', value='@binding(instrument.m2_f)', minimum=65000,
                                          maximum=95000, on_slider_released='slider_release')
        self.objective_tab = ui.create_tab(label='Objective',
                                           content=ui.create_column(self.obj_combo_box, self.m1_slider_labels,
                                                                    self.m1_slider, self.m2_slider_labels,
                                                                    self.m2_slider, ui.create_row(self.full_range_pb,
                                                                                                  ui.create_stretch(),
                                                                                                  self.save_obj_pb)))

        self.sa_combo_box = ui.create_combo_box(name='sa_combo_box', items=['None', '150', '100', '50'],
                                                current_index='@binding(instrument.voa_change_f)')
        self.m3_slider_label = ui.create_label(name='m3_slider_label', text='@binding(instrument.m3_f)')
        self.m3_slider_labels = ui.create_row(self.m3_slider_label, self.m3_range, ui.create_stretch(), spacing=12)
        self.m3_slider = ui.create_slider(name='m3_slider', value='@binding(instrument.m3_f)', minimum=50000,
                                          maximum=140000, on_slider_released='slider_release')
        self.m4_slider_label = ui.create_label(name='m4_slider_label', text='@binding(instrument.m4_f)')
        self.m4_slider_labels = ui.create_row(self.m4_slider_label, self.m4_range, ui.create_stretch(), spacing=12)
        self.m4_slider = ui.create_slider(name='m4_slider', value='@binding(instrument.m4_f)', minimum=40000,
                                          maximum=70000, on_slider_released='slider_release')

        self.sa_tab = ui.create_tab(label='Selected Area',
                                    content=ui.create_column(self.sa_combo_box, self.m3_slider_labels, self.m3_slider,
                                                             self.m4_slider_labels, self.m4_slider,
                                                             ui.create_row(self.full_range_pb, ui.create_stretch(),
                                                                           self.save_sa_pb)))

        self.tabs = ui.create_tabs(self.objective_tab, self.sa_tab)
        self.ui_view = ui.create_column(self.tabs)

def create_spectro_panel(document_controller, panel_id, properties):
    instrument = properties["instrument"]
    ui_handler = diafhandler(instrument, document_controller.event_loop)
    ui_view = diafView(instrument)
    panel = Panel.Panel(document_controller, panel_id, properties)

    finishes = list()
    panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)

    for finish in finishes:
        finish()
    if ui_handler and hasattr(ui_handler, "init_handler"):
        ui_handler.init_handler()
    return panel


def run(instrument: diaf_inst.diafDevice) -> None:
    panel_id = "Apertures"  # make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Apertures")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
