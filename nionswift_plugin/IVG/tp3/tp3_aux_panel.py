# standard libraries
import gettext

from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface

from . import tp3func

_ = gettext.gettext

class TP3handler:

    def __init__(self, instrument: tp3func.TimePix3, document_controller):

        self.event_loop = document_controller.event_loop
        self.document_controller = document_controller
        self.instrument = instrument
        self.enabled = False
        #print(dir(instrument))
        #self.property_changed_event_listener = self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        #self.busy_event_listener = self.instrument.busy_event.listen(self.prepare_widget_disable)

    async def do_enable(self, enabled=True, not_affected_widget_name_list=None):
        for var in self.__dict__:
            if var not in not_affected_widget_name_list:
                if isinstance(getattr(self, var), UserInterface.Widget):
                    widg = getattr(self, var)
                    setattr(widg, "enabled", enabled)

    async def data_item_show(self, DI):
        self.document_controller.document_model.append_data_item(DI)

    def init_handler(self):
        pass

    def changed_controller(self, widget, current_index):
        if self.controller_value.current_item == 'usim_stem_controller':
            self.start_button.enabled = False
        else:
            self.start_button.enabled = True
        self.trigger_value.items = self.__cams[current_index]

    def prepare_widget_enable(self, value):
        self.event_loop.create_task(self.do_enable(True, ['start_button', 'cancel_button']))

    def prepare_widget_disable(self, value):
        self.event_loop.create_task(self.do_enable(False, []))

    def slider_release(self, widget):
        if widget == self.delay_slider:
            print('delay')
        elif widget == self.width_slider:
            print('widtth')


class TP3View:

    def __init__(self, instrument: tp3func.TimePix3):
        ui = Declarative.DeclarativeUI()

        current_label = ui.create_label(text='Current (pA): ')
        current_val = ui.create_label(text="0.00")
        current_row = ui.create_row(current_label, current_val, ui.create_stretch())

        delay_label = ui.create_label(text='Time Delay: ')
        delay_label_value = ui.create_label(name='delay_label_value', text="0.00")
        delay_row = ui.create_row(delay_label, delay_label_value, ui.create_stretch())
        delay_slider = ui.create_slider(name='delay_slider', value=0,
                                        on_slider_released="slider_release")

        width_label = ui.create_label(text='Time width: ')
        width_label_value = ui.create_label(name='width_label_value', text="0.00")
        width_row = ui.create_row(width_label, width_label_value, ui.create_stretch())
        width_slider = ui.create_slider(name='width_slider',
                                        on_slider_released="slider_release", maximum=1000000000)



        self.ui_view = ui.create_column(current_row, delay_row, delay_slider, width_row, width_slider, spacing=5)


def create_spectro_panel(document_controller, panel_id, properties):
    instrument = properties["instrument"]
    ui_handler = TP3handler(instrument, document_controller)
    ui_view = TP3View(instrument)
    panel = Panel.Panel(document_controller, panel_id, properties)

    finishes = list()
    panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)

    for finish in finishes:
        finish()
    if ui_handler and hasattr(ui_handler, "init_handler"):
        ui_handler.init_handler()
    return panel


def run() -> None:
    panel_id = "TimePix3 Settings"  # make sure it is unique, otherwise only one of the panel will be displayed
    name = _("TimePix3 Settings")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": tp3func.TimePix3})
