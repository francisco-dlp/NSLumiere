# standard libraries
import gettext
import os
import json

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.utils import Registry
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.swift.model import HardwareSource
from nion.swift.model import DataItem
import numpy
import time

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
        self.spim_over_listener = self.instrument.spim_over.listen(self.over_spim)

    async def do_enable(self, enabled=True, not_affected_widget_name_list=None):
        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self, var), UserInterface.Widget):
                    widg=getattr(self, var)
                    setattr(widg, "enabled", enabled)

    async def data_item_show(self, DI):
        self.document_controller.document_model.append_data_item(DI)

    def init_handler(self):
        self.__cams = []
        self.__scans = []
        self.__controllers = dict()

        my_insts = Registry.get_components_by_type("stem_controller")
        for counter, my_inst in enumerate(list(my_insts)):
            self.__controllers[my_inst.instrument_id] = counter
            self.__cams.append([])
            self.__scans.append([])

        for hards in HardwareSource.HardwareSourceManager().hardware_sources:  # finding eels camera. If you don't
            if hasattr(hards, 'hardware_source_id'):
                if hasattr(hards, '_CameraHardwareSource__instrument_controller_id'):
                    self.__cams[self.__controllers[hards._CameraHardwareSource__instrument_controller_id]].append(hards._HardwareSource__display_name)
                if hasattr(hards, '_ScanHardwareSource__stem_controller'):
                    self.__scans[self.__controllers[hards._ScanHardwareSource__stem_controller.instrument_id]].append(hards.hardware_source_id)


        self.controller_value.items = self.__controllers

        self.start_button.enabled=False
        self.cancel_button.enabled=False

        if self.controller_value.current_item == 'usim_stem_controller':
            self.start_button.enabled=False
        else:
            self.start_button.enabled=True


    def changed_controller(self, widget, current_index):
        if self.controller_value.current_item == 'usim_stem_controller':
            self.start_button.enabled=False
        else:
            self.start_button.enabled=True
        self.trigger_value.items = self.__cams[current_index]

    def prepare_widget_enable(self,  value):
        self.event_loop.create_task(self.do_enable(True, ['start_button', 'cancel_button']))

    def prepare_widget_disable(self, value):
        self.event_loop.create_task(self.do_enable(False, []))

    def over_spim(self, imagedata, spim_pixels, detector, sampling):
        self.event_loop.create_task(self.do_enable(False, []))
        self.event_loop.create_task(self.do_enable(True, ['cancel_button']))
        for det in detector:
            calib = Calibration.Calibration()
            dim_calib = [Calibration.Calibration(), Calibration.Calibration()]
            dim_calib[0].scale = sampling[0]
            dim_calib[1].scale = sampling[1]
            dim_calib[0].units = 'nm'
            dim_calib[1].units = 'nm'
            xdata = DataAndMetadata.new_data_and_metadata(imagedata[det*spim_pixels[1]:(det + 1)*spim_pixels[1], 0: spim_pixels[0]].astype(numpy.float32), calib, dim_calib)
            data_item = DataItem.DataItem()
            data_item.set_xdata(xdata)
            data_item.define_property("title", 'Spim Image')
            self.event_loop.create_task(self.data_item_show(data_item))

    def cancel_spim(self, widget):
        self.instrument.stop_spim_push_button()
        self.start_button.enabled=True
        self.cancel_button.enabled=False

    def start_spim(self, widget):
        self.instrument.start_spim_push_button(self.x_pixels_value.text, self.y_pixels_value.text)
        self.start_button.enabled=False
        self.cancel_button.enabled=True

class ivgSpimView:


    def __init__(self, instrument:ivg_inst.ivgInstrument):
        ui = Declarative.DeclarativeUI()

        self.controller_label = ui.create_label(name='controller_label', text='Controller: ')
        self.controller_value = ui.create_combo_box(name='controller_value', items=['Controllers'], on_current_index_changed='changed_controller')
        self.controller_row = ui.create_row(self.controller_label, self.controller_value, ui.create_stretch(), spacing=12)

        self.type_label=ui.create_label(name='type_label', text='Type: ')
        self.type_value=ui.create_combo_box(name='type_value', items=['Normal', 'Random', 'User-Defined'], current_index='@binding(instrument.spim_type_f)')
        self.subscan_label = ui.create_label(name='subscan_label', text='From Subscan: ')
        self.subscan_value = ui.create_label(name='subscan_value', text='@binding(instrument.is_subscan_f)')
        self.type_column = ui.create_row(self.type_label, self.type_value, ui.create_spacing(12), self.subscan_label, self.subscan_value, ui.create_stretch())

        self.trigger_label=ui.create_label(name='trigger_label', text='Trigger: ')
        self.trigger_value=ui.create_combo_box(name='trigger_value', items=['EELS', 'EIRE', 'EELS+EIRE'], current_index='@binding(instrument.spim_trigger_f)')
        self.trigger_column = ui.create_row(self.trigger_label, self.trigger_value, ui.create_stretch())

        self.x_pixels_label = ui.create_label(name='x_pixels_label', text='x Pixels: ')
        self.x_pixels_value = ui.create_line_edit(name='x_pixels_value', text='@binding(instrument.spim_xpix_f)')
        self.y_pixels_label = ui.create_label(name='y_pixels_label', text='y Pixels: ')
        self.y_pixels_value = ui.create_line_edit(name='y_pixels_value', text='@binding(instrument.spim_ypix_f)')
        self.pixels_column = ui.create_row(self.x_pixels_label, self.x_pixels_value, ui.create_stretch(), self.y_pixels_label, self.y_pixels_value, ui.create_stretch())

        self.sampling_label = ui.create_label(name='sampling_label', text='Sampling (nm): ')
        self.sampling_value = ui.create_label(name='sampling_value', text='@binding(instrument.spim_sampling_f)')
        self.sampling_row = ui.create_row(self.sampling_label, self.sampling_value, ui.create_stretch())

        self.time_label = ui.create_label(name='time_label', text='Estimated Time (min): ')
        self.time_value = ui.create_label(name='time_value', text='@binding(instrument.spim_time_f)')
        self.time_row = ui.create_row(self.time_label, self.time_value, ui.create_stretch())

        self.bottom_blanker = ui.create_check_box(name='bottom_blanker_value', text='Bottom Blanker', checked='@binding(instrument.is_blanked)')

        self.cancel_button = ui.create_push_button(name='cancel_button', text='Cancel', on_clicked='cancel_spim')
        self.start_button = ui.create_push_button(name='start_button', text='Start', on_clicked='start_spim')
        self.button_row = ui.create_row(ui.create_stretch(), self.cancel_button, self.start_button, spacing=5)

        self.ui_view=ui.create_column(self.controller_row, self.type_column, self.trigger_column, self.pixels_column, self.sampling_row, self.time_row, self.bottom_blanker, self.button_row, spacing=5)
        
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
