# standard libraries
import gettext
import os
import json
import numpy

from nion.swift import Panel
from nion.swift import Workspace
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.swift.model import DataItem
from nion.swift.model import Utility

from . import ivg_inst

_ = gettext.gettext

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

MAX_PTS = settings["IVG"]["MAX_PTS"]
STAGE_MATRIX_SIZE = settings["IVG"]["STAGE_MATRIX_SIZE"]

class ivgSpimhandler:


    def __init__(self,instrument:ivg_inst.ivgInstrument, document_controller):

        self.event_loop=document_controller.event_loop
        self.document_controller=document_controller
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

    def cancel_spim(self, widget):
        self.instrument.stop_spim_push_button()

    def start_spim(self, widget):
        self.instrument.start_spim_push_button(self.x_pixels_value.text, self.y_pixels_value.text, self.type_value.current_index, self.trigger_value.current_index)

class ivgSpimView:


    def __init__(self, instrument:ivg_inst.ivgInstrument):
        ui = Declarative.DeclarativeUI()
        
        self.type_label=ui.create_label(name='type_label', text='Type: ')
        self.type_value=ui.create_combo_box(name='type_value', items=['Normal', 'Random', 'User-Defined'], current_index='@binding(instrument.spim_type_f)')
        self.type_column = ui.create_row(self.type_label, self.type_value, ui.create_stretch())

        self.trigger_label=ui.create_label(name='trigger_label', text='Trigger: ')
        self.trigger_value=ui.create_combo_box(name='trigger_value', items=['EELS', 'CL', 'EELS+CL'], current_index='@binding(instrument.spim_trigger_f)')
        self.trigger_column = ui.create_row(self.trigger_label, self.trigger_value, ui.create_stretch())

        self.x_pixels_label = ui.create_label(name='x_pixels_label', text='x Pixels: ')
        self.x_pixels_value = ui.create_line_edit(name='x_pixels_value', text='@binding(instrument.spim_xpix_f)')
        self.y_pixels_label = ui.create_label(name='y_pixels_label', text='y Pixels: ')
        self.y_pixels_value = ui.create_line_edit(name='y_pixels_value', text='@binding(instrument.spim_ypix_f)')
        self.pixels_column = ui.create_row(self.x_pixels_label, self.x_pixels_value, ui.create_stretch(), self.y_pixels_label, self.y_pixels_value, ui.create_stretch())

        self.sampling_label = ui.create_label(name='sampling_label', text='Sampling (nm): ')
        self.sampling_value = ui.create_label(name='sampling_value', text='41.57')
        self.sampling_row = ui.create_row(self.sampling_label, self.sampling_value, ui.create_stretch())

        self.bottom_blanker = ui.create_check_box(name='bottom_blanker_value', text='Bottom Blanker', checked='@binding(instrument.is_blanked)')

        self.cancel_button = ui.create_push_button(name='cancel_button', text='Cancel', on_clicked='cancel_spim')
        self.start_button = ui.create_push_button(name='start_button', text='Start', on_clicked='start_spim')
        self.button_row = ui.create_row(ui.create_stretch(), self.cancel_button, self.start_button, spacing=5)

        self.ui_view=ui.create_column(self.type_column, self.trigger_column, self.pixels_column, self.sampling_row, self.bottom_blanker, self.button_row, spacing=5)
        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =ivgSpimhandler(instrument, document_controller)
        ui_view=ivgSpimView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: ivg_inst.ivgInstrument) -> None:
    panel_id = "Orsay Spectral Image"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Orsay Spectral Image")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
