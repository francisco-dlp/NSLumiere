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


    async def do_enable(self,enabled=True,not_affected_widget_name_list=None):
        #Pythonic way of finding the widgets
        #actually a more straigthforward way would be to create a list of widget in the init_handler
        #then use this list in the present function...
        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self,var),UserInterface.Widget):
                    widg=getattr(self,var)
                    setattr(widg, "enabled", enabled)

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, []))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, []))

class stageView:


    def __init__(self, instrument:stage_inst.stageDevice):
        ui = Declarative.DeclarativeUI()

        ## wobbler ##
        self.wobbler_value = ui.create_line_edit(name='wobbler_value', width=150, text='123')
        self.wobbler_slider_label=ui.create_label(name='wobbler_slider_label', text='Frequency [Hz]: ')
        self.wobbler_value_label=ui.create_label(name='wobbler_value_label', text='01234')
        self.wobbler_slider_frequency=ui.create_slider(name='wobbler_slider_frequency', value='51515', minimum=1, maximum=10)
        self.wobbler_freq_row = ui.create_row(self.wobbler_slider_label, self.wobbler_value_label)
		
        self.ui_view=ui.create_column(self.wobbler_value, self.wobbler_freq_row, self.wobbler_slider_frequency)



        
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
