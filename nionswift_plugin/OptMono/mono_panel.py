# standard libraries
import gettext
import os
import json

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface

from . import mono_inst
_ = gettext.gettext

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)
GRATINGS = settings["MONOCHROMATOR"]["GRATINGS"]

print(GRATINGS)

class Monohandler:


    def __init__(self, instrument:mono_inst.MonoDevice, event_loop):

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
        self.event_loop.create_task(self.do_enable(True, ['init_pb']))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, ['init_pb']))

    def init_handler(self):
        self.event_loop.create_task(self.do_enable(False, ['init_pb']))

    def init(self, widget):
        self.init_pb.enabled = False
        abs_path = os.path.abspath(os.path.join((__file__ + "/../../"), 'global_settings.json'))
        with open(abs_path) as savfile:
            settings = json.load(savfile)
        GRATINGS = settings["MONOCHROMATOR"]["GRATINGS"]
        self.event_loop.create_task(self.do_enable(True, ['init_pb']))
        self.instrument.init()

class MonoView:


    def __init__(self, instrument:mono_inst.MonoDevice):
        ui = Declarative.DeclarativeUI()

        self.init_pb = ui.create_push_button(name='init_pb', text='Init Hardware', on_clicked='init')

        self.wl_label = ui.create_label(text='Wavelength (nm): ', name='wl_label')
        self.wl_value = ui.create_line_edit(name='wl_value', text='@binding(instrument.wav_f)')
        self.wl_row=ui.create_row(self.wl_label, self.wl_value, ui.create_stretch())

        self.gratings_label=ui.create_label(name='gratings_label', text='Grating: ')
        self.gratings_combo_box=ui.create_combo_box(name='gratings_combo_box', items=GRATINGS,
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

        self.ui_view=ui.create_column(
            self.init_pb,
            self.wl_row,
            self.gratings_row,
            self.slit_row,
            self.slit_choice_row)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =Monohandler(instrument, document_controller.event_loop)
        ui_view=MonoView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: mono_inst.MonoDevice) -> None:
    panel_id = "Monochromator"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Monochromator")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
