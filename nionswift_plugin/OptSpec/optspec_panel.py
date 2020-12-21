# standard libraries
import gettext

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface

from . import optspec_inst
_ = gettext.gettext

GRATINGS = list()

class OptSpechandler:


    def __init__(self, instrument:optspec_inst.OptSpecDevice, event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.send_gratings_listener = self.instrument.send_gratings.listen(self.receive_gratings)

    async def do_enable(self,enabled=True,not_affected_widget_name_list=None):

        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self,var),UserInterface.Widget):
                    widg=getattr(self,var)
                    setattr(widg, "enabled", enabled)

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, ['init_pb']))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, ['init_pb']))

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

    def receive_gratings(self, grat_received):
        GRATINGS = grat_received
        self.gratings_combo_box.items = GRATINGS

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

        self.main_tab=ui.create_tab(label='Main', content=ui.create_column(
            self.pb_row,
            self.wl_row,
            self.gratings_row,
            self.slit_row,
            self.slit_choice_row))

        #Second TAB

        self.focal_length_label = ui.create_label(name='focal_length_label', text='Spec. FL (mm): ')
        self.focal_length_value = ui.create_line_edit(name='focal_length_value',
                                                      text='@binding(instrument.focalLength_f)')
        self.focal_length_row = ui.create_row(self.focal_length_label, self.focal_length_value, ui.create_stretch())

        self.camsize_label = ui.create_label(name='camsize_label', text='Hor. Camera Size (mm): ')
        self.camsize_value = ui.create_line_edit(name='camsize_value',
                                                      text='@binding(instrument.camera_size_f)')
        self.camsize_row = ui.create_row(self.camsize_label, self.camsize_value, ui.create_stretch())

        self.campixels_label = ui.create_label(name='campixels_label', text='Hor. Camera Pixels: ')
        self.campixels_value = ui.create_line_edit(name='campixels_value',
                                                      text='@binding(instrument.camera_pixels_f)')
        self.campixels_row = ui.create_row(self.campixels_label, self.campixels_value, ui.create_stretch())


        self.setting_tab = ui.create_tab(label='Settings', content=ui.create_column(
            self.focal_length_row, self.camsize_row, self.campixels_row))


        #THIRD TAB

        self.upt_pb02 = ui.create_push_button(name='upt_pb02', text='Update', on_clicked='upt_info')

        self.disp_label = ui.create_label(name='disp_label', text='Dispersion (nm/mm): ')
        self.disp_value = ui.create_label(name='disp_value', text='@binding(instrument.dispersion_nmmm_f)')
        self.disp_row = ui.create_row(self.disp_label, self.disp_value, ui.create_stretch())

        self.pixelSize_label = ui.create_label(name='pixelSize_label', text='Pixel Size (um): ')
        self.pixelSize_value = ui.create_label(name='pixelSize_value', text='@binding(instrument.pixel_size_f)')
        self.pixelSize_row = ui.create_row(self.pixelSize_label, self.pixelSize_value, ui.create_stretch())

        self.dispersion_pixel_label = ui.create_label(name='dispersion_pixel_label', text='Dispersion (nm/pixels): ')
        self.dispersion_pixel_value = ui.create_label(name='dispersion_pixels_label', text='@binding(instrument.dispersion_pixels_f)')
        self.dispersion_pixel_row = ui.create_row(self.dispersion_pixel_label, self.dispersion_pixel_value, ui.create_stretch())

        self.range_label = ui.create_label(name='range_label', text='Range (nm): ')
        self.range_value = ui.create_label(name='range_value', text='@binding(instrument.fov_f)')
        self.range_row = ui.create_row(self.range_label, self.range_value, ui.create_stretch())

        self.info_tab = ui.create_tab(label='Info', content=ui.create_column(
            self.upt_pb02,
            self.disp_row,
            self.pixelSize_row, self.dispersion_pixel_row, self.range_row))

        self.tabs = ui.create_tabs(self.main_tab, self.info_tab, self.setting_tab)

        self.ui_view = ui.create_column(self.tabs)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =OptSpechandler(instrument, document_controller.event_loop)
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
