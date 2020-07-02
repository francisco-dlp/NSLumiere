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

from . import scan_inst
import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class scanhandler:


    def __init__(self, instrument:scan_inst.scanDevice, event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)


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


class scanView:


    def __init__(self, instrument:scan_inst.scanDevice):
        ui = Declarative.DeclarativeUI()

        ### Full Range ###


        ### SLIDERS ###

        self.field_label = ui.create_label(name='x_label', text='X Pos: ')
        self.field_value_edit = ui.create_line_edit(name='x_value_edit', text='@binding(instrument.field_edit_f)')
        self.field_row=ui.create_row(self.field_label, self.field_value_edit, ui.create_stretch())
        self.field_slider=ui.create_slider(name='x_slider', value='@binding(instrument.field_f)', minimum=0, maximum=1000000)


        self.ui_view=ui.create_column(self.field_row, self.field_slider, ui.create_spacing(10))



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =scanhandler(instrument, document_controller.event_loop)
        ui_view=scanView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: scan_inst.scanDevice) -> None:
    panel_id = "Scan Lumiere"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Scan Lumiere")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
