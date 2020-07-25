# standard libraries
import gettext
import os
import json

# local libraries
from nion.swift import Panel
from nion.swift import Workspace
from nion.ui import Declarative
from nion.ui import UserInterface
from . import mirror_inst

_ = gettext.gettext


class mirrorhandler:

    def __init__(self, instrument: mirror_inst.mirrorDevice, event_loop):

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
        panel_dir = os.path.dirname(__file__)
        abs_path = os.path.join(panel_dir, 'mirror_settings.json')
        with open(abs_path) as savfile:
            json_object = json.load(savfile)

        #json_object['ROA'][self.obj_combo_box.current_item] = {"m1": self.m1_slider.value, "m2": self.m2_slider.value}
        #json_object['ROA']['last'] = self.obj_combo_box.current_index

        with open(abs_path, 'w') as json_file:
            json.dump(json_object, json_file, indent=4)

        self.total_range(widget)

    def save_SA(self, widget):
        panel_dir = os.path.dirname(__file__)
        abs_path = os.path.join(panel_dir, 'mirror_settings.json')
        with open(abs_path) as savfile:
            json_object = json.load(savfile)  # data is load json

        #json_object['VOA'][self.sa_combo_box.current_item] = {"m3": self.m3_slider.value, "m4": self.m4_slider.value}
        #json_object['VOA']['last'] = self.sa_combo_box.current_index

        with open(abs_path, 'w') as json_file:
            json.dump(json_object, json_file, indent=4)

        self.total_range(widget)

    def total_range_2(self):
        self.m1_slider.maximum = 130000
        self.m1_slider.minimum = 40000

        self.m2_slider.maximum = 95000
        self.m2_slider.minimum = 65000

        self.m3_slider.maximum = 140000
        self.m3_slider.minimum = 50000

        self.m4_slider.maximum = 70000
        self.m4_slider.minimum = 40000

    def total_range(self, widget):
        self.m1_slider.maximum = 130000
        self.m1_slider.minimum = 40000

        self.m2_slider.maximum = 95000
        self.m2_slider.minimum = 65000

        self.m3_slider.maximum = 140000
        self.m3_slider.minimum = 50000

        self.m4_slider.maximum = 70000
        self.m4_slider.minimum = 40000

    def slider_release(self, widget):
        widget.maximum = widget.value + 2000
        widget.minimum = widget.value - 2000

    def x_min(self, widget):
        self.instrument.x_f-=self.instrument.x_rel_f

    def x_max(self, widget):
        self.instrument.x_f+=self.instrument.x_rel_f

    def y_min(self, widget):
        self.instrument.y_f -= self.instrument.y_rel_f

    def y_max(self, widget):
        self.instrument.y_f += self.instrument.y_rel_f

    def z_min(self, widget):
        self.instrument.z_f -= self.instrument.z_rel_f

    def z_max(self, widget):
        self.instrument.z_f += self.instrument.z_rel_f


class mirrorView:

    def __init__(self, instrument: mirror_inst.mirrorDevice):
        ui = Declarative.DeclarativeUI()

        self.x_pos_label = ui.create_label(name='x_pos_label', text='Position: ')
        self.x_pos_value = ui.create_line_edit(name='x_pos_value', text='@binding(instrument.x_f)')
        self.x_pos_row = ui.create_row(self.x_pos_label, self.x_pos_value, ui.create_stretch())

        self.x_pos_rel_min = ui.create_push_button(name='x_pos_rel_min', text='<<', on_clicked='x_min')
        self.x_pos_rel_value = ui.create_line_edit(name='x_pos_rel_value', text='@binding(instrument.x_rel_f)')
        self.x_pos_rel_max = ui.create_push_button(name='x_pos_rel_max', text='>>', on_clicked='x_max')
        self.x_pos_rel_row = ui.create_row(self.x_pos_rel_min, self.x_pos_rel_value, self.x_pos_rel_max)

        self.x_group = ui.create_group(title='Motor X', content=ui.create_column(
            self.x_pos_row, self.x_pos_rel_row
        ))

        self.y_pos_label = ui.create_label(name='y_pos_label', text='Position: ')
        self.y_pos_value = ui.create_line_edit(name='y_pos_value', text='@binding(instrument.y_f)')
        self.y_pos_row = ui.create_row(self.y_pos_label, self.y_pos_value, ui.create_stretch())

        self.y_pos_rel_min = ui.create_push_button(name='y_pos_rel_min', text='<<', on_clicked='y_min')
        self.y_pos_rel_value = ui.create_line_edit(name='y_pos_rel_value', text='@binding(instrument.y_rel_f)')
        self.y_pos_rel_max = ui.create_push_button(name='y_pos_rel_max', text='>>', on_clicked='y_max')
        self.y_pos_rel_row = ui.create_row(self.y_pos_rel_min, self.y_pos_rel_value, self.y_pos_rel_max)

        self.y_group = ui.create_group(title='Motor Y', content=ui.create_column(
            self.y_pos_row, self.y_pos_rel_row
        ))

        self.z_pos_label = ui.create_label(name='z_pos_label', text='Position: ')
        self.z_pos_value = ui.create_line_edit(name='z_pos_value', text='@binding(instrument.z_f)')
        self.z_pos_row = ui.create_row(self.z_pos_label, self.z_pos_value, ui.create_stretch())

        self.z_pos_rel_min = ui.create_push_button(name='z_pos_rel_min', text='<<', on_clicked='z_min')
        self.z_pos_rel_value = ui.create_line_edit(name='z_pos_rel_value', text='@binding(instrument.z_rel_f)')
        self.z_pos_rel_max = ui.create_push_button(name='z_pos_rel_max', text='>>', on_clicked='z_max')
        self.z_pos_rel_row = ui.create_row(self.z_pos_rel_min, self.z_pos_rel_value, self.z_pos_rel_max)

        self.z_group = ui.create_group(title='Motor Z', content=ui.create_column(
            self.z_pos_row, self.z_pos_rel_row
        ))

        self.main_tab = ui.create_tab(label='Main', content=ui.create_column(self.x_group, self.y_group, self.z_group))

        self.tabs = ui.create_tabs(self.main_tab)

        self.ui_view = ui.create_column(self.tabs)


def create_spectro_panel(document_controller, panel_id, properties):
    instrument = properties["instrument"]
    ui_handler = mirrorhandler(instrument, document_controller.event_loop)
    ui_view = mirrorView(instrument)
    panel = Panel.Panel(document_controller, panel_id, properties)

    finishes = list()
    panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)

    for finish in finishes:
        finish()
    if ui_handler and hasattr(ui_handler, "init_handler"):
        ui_handler.init_handler()
    return panel


def run(instrument: mirror_inst.mirrorDevice) -> None:
    panel_id = "Mirror Control"  # make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Mirror Control")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
