# standard libraries
import gettext
import logging
import numpy

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.swift.model import Utility
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.swift.model import DataItem

from . import optspec_inst
_ = gettext.gettext

GRATINGS = list()

class OptSpechandler:


    def __init__(self, instrument:optspec_inst.OptSpecDevice, document_controller):

        self.event_loop = document_controller.event_loop
        self.document_controller = document_controller
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.send_gratings_listener = self.instrument.send_gratings.listen(self.receive_gratings)
        self.warn_panel_listener = self.instrument.warn_panel.listen(self.prepare_data)
        self.send_data_listener = self.instrument.send_data.listen(self.receive_data)
        self.warn_panel_over_listener = self.instrument.warn_panel_over.listen(self.finish_data)

    async def do_enable(self,enabled=True,not_affected_widget_name_list=None):

        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self,var),UserInterface.Widget):
                    widg=getattr(self,var)
                    setattr(widg, "enabled", enabled)

    async def data_item_show(self, DI):
        self.document_controller.document_model.append_data_item(DI)

    async def data_item_exit_live(self, DI):
        DI._exit_live_state()

    async def data_item_remove(self, DI):
        self.document_controller.document_model.remove_data_item(DI)

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, ['init_pb']))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, ['init_pb', 'abort_pb']))

    def init_handler(self):
        self.event_loop.create_task(self.do_enable(False, ['init_pb']))

    def init(self, widget):
        if self.instrument.init():
            self.init_pb.enabled = False
            self.event_loop.create_task(self.do_enable(True, ['init_pb']))
            self.instrument.upt()
        else:
            logging.info('***OPT SPECTROMETER***: Check if camera and spectrometer are connected.')

    def upt(self, widget):
        self.instrument.upt()

    def upt_info(self, widget):
        self.instrument.upt_info()

    def measure(self, widget):
        self.instrument.measure()

    def abort(self, widget):
        self.instrument.abort()

    def receive_gratings(self, grat_received):
        GRATINGS = grat_received
        self.gratings_combo_box.items = GRATINGS

    def prepare_data(self):
        self.array = numpy.zeros(200)

        self.timezone = Utility.get_local_timezone()
        self.timezone_offset = Utility.TimezoneMinutesToStringConverter().convert(Utility.local_utcoffset_minutes())
        self.xdata = DataAndMetadata.new_data_and_metadata(self.array, timezone=self.timezone, timezone_offset=self.timezone_offset)
        self.data_item = DataItem.DataItem()
        self.data_item.set_xdata(self.xdata)
        self.data_item._enter_live_state()

        self.event_loop.create_task(self.data_item_show(self.data_item))


    def receive_data(self, value, index):
        if index == 0:
            self.array = numpy.zeros(200)
        self.array[index] = value
        self.data_item.set_data(self.array)

    def finish_data(self):
        if self.data_item:
            self.event_loop.create_task(self.data_item_exit_live(self.data_item))
            self.event_loop.create_task(self.data_item_remove(self.data_item))
            self.data_item = None

class OptSpecView:

    def __init__(self, instrument:optspec_inst.OptSpecDevice):
        ui = Declarative.DeclarativeUI()

        self.init_pb = ui.create_push_button(name='init_pb', text='Init Hardware', on_clicked='init')
        self.upt_pb = ui.create_push_button(name='upt_pb', text='Update', on_clicked='upt')
        self.pb_row = ui.create_row(self.init_pb, self.upt_pb)

        self.wl_label = ui.create_label(text='Wavelength (nm): ', name='wl_label')
        self.wl_value = ui.create_line_edit(name='wl_value', text='@binding(instrument.wav_f)')
        self.wl_row=ui.create_row(self.wl_label, self.wl_value, ui.create_stretch())

        self.gratings_label=ui.create_label(name='gratings_label', text='Grating: ')
        self.gratings_combo_box=ui.create_combo_box(name='gratings_combo_box', items=GRATINGS, width=150,
                                                    current_index='@binding(instrument.grating_f)')
        self.gratings_row=ui.create_row(self.gratings_label, self.gratings_combo_box, ui.create_stretch())

        self.entrance_slit_label=ui.create_label(name='entrance_slit_label', text='Entrance Slit: ')
        self.entrance_slit_value = ui.create_line_edit(name='entrance_slit_value',
                                                       text='@binding(instrument.entrance_slit_f)')
        self.exit_slit_label = ui.create_label(name='exit_slit_label', text='Exit Slit: ')
        self.exit_slit_value = ui.create_line_edit(name='exit_slit_value',
                                                       text='@binding(instrument.exit_slit_f)')

        self.slit_row = ui.create_row(self.entrance_slit_label, self.entrance_slit_value,
                      ui.create_spacing(15),
                      self.exit_slit_label, self.exit_slit_value)


        self.slit_choice = ui.create_combo_box(text='Exit: ', name='slit_choice',
                                               items=['Axial', 'Lateral'],
                                               current_index='@binding(instrument.which_slit_f)')

        self.slit_choice_row = ui.create_row(self.slit_choice, ui.create_stretch())

        self.main_group = ui.create_group(title='Main', content=ui.create_column(
            self.pb_row,
            self.wl_row,
            self.gratings_row,
            self.slit_row,
            self.slit_choice_row))

        ## Info group

        self.grove_label = ui.create_label(name='grove_label', text='Groove (lp/mm): ')
        self.grove_value = ui.create_label(name='grove_value', text='@binding(instrument.lpmm_f)')
        self.grove_row = ui.create_row(self.grove_label, self.grove_value, ui.create_stretch())

        self.disp_label = ui.create_label(name='disp_label', text='Dispersion (nm/mm): ')
        self.disp_value = ui.create_label(name='disp_value', text='@binding(instrument.dispersion_nmmm_f)')
        self.disp_row = ui.create_row(self.disp_label, self.disp_value, ui.create_stretch())

        self.pixelSize_label = ui.create_label(name='pixelSize_label', text='Pixel Size (um): ')
        self.pixelSize_value = ui.create_label(name='pixelSize_value', text='@binding(instrument.pixel_size_f)')
        self.pixelSize_row = ui.create_row(self.pixelSize_label, self.pixelSize_value, ui.create_stretch())

        self.dispersion_pixel_label = ui.create_label(name='dispersion_pixel_label', text='Dispersion (nm/pixels): ')
        self.dispersion_pixel_value = ui.create_label(name='dispersion_pixels_label',
                                                      text='@binding(instrument.dispersion_pixels_f)')
        self.dispersion_pixel_row = ui.create_row(self.dispersion_pixel_label, self.dispersion_pixel_value,
                                                  ui.create_stretch())

        self.range_label = ui.create_label(name='range_label', text='Range (nm): ')
        self.range_value = ui.create_label(name='range_value', text='@binding(instrument.fov_f)')
        self.range_row = ui.create_row(self.range_label, self.range_value, ui.create_stretch())

        self.info_group = ui.create_group(title='Info', content=ui.create_column(
            self.grove_row,
            self.disp_row,
            self.pixelSize_row, self.dispersion_pixel_row, self.range_row, spacing=2))

        ## Settings group

        self.focal_length_label = ui.create_label(name='focal_length_label', text='Spec. FL (mm): ')
        self.focal_length_value = ui.create_line_edit(name='focal_length_value',
                                                      text='@binding(instrument.focalLength_f)', width=50)
        self.focal_length_row = ui.create_row(self.focal_length_label, self.focal_length_value, ui.create_stretch())

        self.camsize_label = ui.create_label(name='camsize_label', text='Hor. Camera Size (mm): ')
        self.camsize_value = ui.create_line_edit(name='camsize_value',
                                                      text='@binding(instrument.camera_size_f)', width=50)
        self.camsize_row = ui.create_row(self.camsize_label, self.camsize_value, ui.create_stretch())

        self.campixels_label = ui.create_label(name='campixels_label', text='Hor. Camera Pixels: ')
        self.campixels_value = ui.create_line_edit(name='campixels_value',
                                                      text='@binding(instrument.camera_pixels_f)', width=50)
        self.campixels_row = ui.create_row(self.campixels_label, self.campixels_value, ui.create_stretch())


        self.settings_group = ui.create_group(title='Settings', content=ui.create_column(
            self.focal_length_row, self.camsize_row, self.campixels_row))

        # Measurement group

        self.meas_pb = ui.create_push_button(name='meas_pb', text='Measure Intensity', on_clicked='measure')
        self.abort_pb = ui.create_push_button(name='abort_pb', text='Abort', on_clicked='abort')
        self.meas_row = ui.create_row(self.meas_pb, self.abort_pb, ui.create_stretch())

        self.meas_group = ui.create_group(title='Alignment', content=ui.create_column(
            self.meas_row))

        self.ui_view = ui.create_column(self.main_group, self.info_group, self.settings_group, self.meas_group)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =OptSpechandler(instrument, document_controller)
        ui_view=OptSpecView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: optspec_inst.OptSpecDevice, name='Optical Spectrometer') -> None:
    panel_id = name
    name = _(name)
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
