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

from . import stage_inst
import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class stagehandler:


    def __init__(self,instrument:stage_inst.stageDevice,event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.slider_max = 2500


    async def do_enable(self,enabled=True,not_affected_widget_name_list=None):

        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self,var),UserInterface.Widget):
                    widg=getattr(self,var)
                    setattr(widg, "enabled", enabled)

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, []))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, []))

    def slider_release(self, widget):
        value=self.instrument.slider_range_f
        widget.maximum=widget.value+value
        widget.minimum=widget.value-value

    def total_range(self, widget):
        self.x_slider.maximum = 80000
        self.x_slider.minimum = -80000

        self.y_slider.maximum = 80000
        self.y_slider.minimum = -80000

    def line_edit(self, widget, text):
        self.total_range(self.add_pb)

    def add_value(self, widget):
        self.list_positions.text+='(' + self.x_value_edit.text +', ' + self.y_value_edit.text + "): \n"

    def set_origin(self, widget):
        self.instrument.set_origin()

class stageView:


    def __init__(self, instrument:stage_inst.stageDevice):
        ui = Declarative.DeclarativeUI()

        ### Buttons ###

        self.full_range_pb=ui.create_push_button(name='full_range_pb', text='Full Range', on_clicked='total_range', width=100)
        self.add_pb=ui.create_push_button(name='add_pb', text='Add', on_clicked='add_value')
        self.set_origin_pb=ui.create_push_button(name='set_origin_pb', text='Set Origin', on_clicked='set_origin')
        self.list_positions=ui.create_text_edit(name='list_positions')
        self.button_row=ui.create_row(ui.create_stretch(), self.set_origin_pb, self.add_pb, self.full_range_pb)


        ### SLIDERS ###

        self.x_label = ui.create_label(name='x_label', text='X Pos: ')
        self.x_value_edit = ui.create_line_edit(name='x_value_edit', text='@binding(instrument.x_pos_edit_f)', on_text_edited='line_edit')
        self.x_row=ui.create_row(self.x_label, self.x_value_edit, ui.create_stretch())
        self.x_slider=ui.create_slider(name='x_slider', value='@binding(instrument.x_pos_f)', minimum=-80000, maximum=80000, on_slider_released='slider_release')

        self.y_label = ui.create_label(name='y_label', text='Y Pos: ')
        self.y_value_edit = ui.create_line_edit(name='y_value_edit', text='@binding(instrument.y_pos_edit_f)', on_text_edited='line_edit')
        self.y_row = ui.create_row(self.y_label, self.y_value_edit, ui.create_stretch())
        self.y_slider = ui.create_slider(name='y_slider', value='@binding(instrument.y_pos_f)', minimum=-80000, maximum=80000, on_slider_released='slider_release')

        self.ui_view=ui.create_column(self.x_row, self.x_slider, ui.create_spacing(10), self.y_row, self.y_slider, self.list_positions, self.button_row)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =stagehandler(instrument, document_controller.event_loop)
        ui_view=stageView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: stage_inst.stageDevice) -> None:
    panel_id = "Stage"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Stage")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
