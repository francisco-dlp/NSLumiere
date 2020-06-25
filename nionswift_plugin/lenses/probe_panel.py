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
import threading

from . import probe_inst
import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class gainhandler:


    def __init__(self,instrument:probe_inst.probeDevice,event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.property_changed_power_event_listener=self.instrument.property_changed_power_event.listen(self.prepare_power_widget_enable)
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
        self.event_loop.create_task(self.do_enable(True, ["init_pb"]))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, ["init_pb", "upt_pb", "abt_pb"]))
    
    def prepare_power_widget_enable(self,value): #NOTE THAT THE SECOND EVENT NEVER WORKS. WHAT IS THE DIF BETWEEN THE FIRST?
        self.event_loop.create_task(self.do_enable(True, ["init_pb"]))
    

    def save_lenses(self, widget):
        l_dict={\
		"100": {"obj": self.obj_value.text, "c1": self.c1_value.text, "c2": self.c2_value.text}\
		}

        panel_dir=os.path.dirname(__file__)
        abs_path=os.path.join(panel_dir, 'lenses_settings.json')
        with open(abs_path, 'w') as json_file:
            json.dump(l_dict, json_file)

    def adj_values(self, widget):
        if widget==self.obj_slider:
            self.obj_slider.maximum=self.obj_slider.value+25000
            self.obj_slider.minimum=max(self.obj_slider.value-25000, 0)
        
        if widget==self.c1_slider:
            self.c1_slider.maximum=self.c1_slider.value+10000
            self.c1_slider.minimum=max(self.c1_slider.value-10000, 0)
        
        if widget==self.c2_slider:
            self.c2_slider.maximum=self.c2_slider.value+10000
            self.c2_slider.minimum=max(self.c2_slider.value-10000, 0)

    def line_update(self, widget, text):
        if widget==self.obj_value:
            if text:
                value=int(float(text)*1000000)
                self.obj_slider.maximum=value+1000000
                self.obj_slider.minimum=max(value-1000000, 0)
        if widget==self.c1_value:
            if text:
                value=int(float(text)*1000000)
                self.c1_slider.maximum=value+500000
                self.c1_slider.minimum=max(value-500000, 0)
        if widget==self.c2_value:
            if text:
                value=int(float(text)*1000000)
                self.c2_slider.maximum=value+500000
                self.c2_slider.minimum=max(value-500000, 0)


class gainView:


    def __init__(self, instrument:probe_inst.probeDevice):
        ui = Declarative.DeclarativeUI()
        
        # fine adjustment #


        ## wobbler ##
        self.wobbler_value = ui.create_line_edit(name='wobbler_value', width=150, text='@binding(instrument.wobbler_intensity_f)')
        self.wobbler_slider_label=ui.create_label(name='wobbler_slider_label', text='Frequency [Hz]: ')
        self.wobbler_value_label=ui.create_label(name='wobbler_value_label', text='@binding(instrument.wobbler_frequency_f)')
        self.wobbler_slider_frequency=ui.create_slider(name='wobbler_slider_frequency', value='@binding(instrument.wobbler_frequency_f)', minimum=1, maximum=10)
        self.wobbler_freq_row = ui.create_row(self.wobbler_slider_label, self.wobbler_value_label)
		
        ## objetive ##

        self.obj_cb = ui.create_check_box(text='Obj:', name='obj_label', checked='@binding(instrument.obj_global_f)')
        self.obj_value = ui.create_line_edit(name='obj_value', text='@binding(instrument.obj_edit_f)', on_text_edited='line_update')
        self.obj_row = ui.create_row(self.obj_cb, self.obj_value)
		
        self.obj_slider = ui.create_slider(name='obj_slider', value='@binding(instrument.obj_slider_f)', minimum=5000000, maximum=9000000, on_slider_released='adj_values')
		
        self.obj_wobbler_cb = ui.create_check_box(text='Wobbler [Obj]: ', name='obj_wobbler_label', checked='@binding(instrument.obj_wobbler_f)')
		
        self.save_pb=ui.create_push_button(text='Save Settings', name='save_pb', on_clicked="save_lenses")
		
        self.obj_wobbler_row = ui.create_row(self.obj_wobbler_cb, self.wobbler_value)
		
        self.objective_tab = ui.create_tab(label='Objective', content=ui.create_column(ui.create_spacing(10), self.obj_row, self.obj_slider, self.obj_wobbler_row, self.wobbler_freq_row, self.wobbler_slider_frequency, ui.create_spacing(10), self.save_pb))
		
	## condensers ##	
		
		
        self.c1_cb = ui.create_check_box(text='C1:', name='c1_label', checked='@binding(instrument.c1_global_f)')
        self.c1_value = ui.create_line_edit(name='c1_value', text='@binding(instrument.c1_edit_f)', on_text_edited='line_update')
        self.c1_row = ui.create_row(self.c1_cb, self.c1_value)
		
        self.c1_slider = ui.create_slider(name='c1_slider', value='@binding(instrument.c1_slider_f)', maximum=1000000, on_slider_released='adj_values')
		
        self.c1_wobbler_cb = ui.create_check_box(text='Wobbler [C1]: ', name='c1_wobbler_label', checked='@binding(instrument.c1_wobbler_f)')
        self.c1_wobbler_row = ui.create_row(self.c1_wobbler_cb, self.wobbler_value)
		
        self.c2_cb = ui.create_check_box(text='C2:', name='c2_label', checked='@binding(instrument.c2_global_f)')
        self.c2_value = ui.create_line_edit(name='c2_value', text='@binding(instrument.c2_edit_f)', on_text_edited='line_update')
        self.c2_row = ui.create_row(self.c2_cb, self.c2_value)
		
        self.c2_slider = ui.create_slider(name='c2_slider', value='@binding(instrument.c2_slider_f)', maximum=1000000, on_slider_released='adj_values')
		
        self.c2_wobbler_cb = ui.create_check_box(text='Wobbler [C2]: ', name='c2_wobbler_label', checked='@binding(instrument.c2_wobbler_f)')
        self.c2_wobbler_row = ui.create_row(self.c2_wobbler_cb, self.wobbler_value)

        self.condenser_tab = ui.create_tab(label='Condenser', content=ui.create_column(ui.create_spacing(10), self.c1_row, self.c1_slider, self.c1_wobbler_row, self.wobbler_freq_row, self.wobbler_slider_frequency, ui.create_spacing(50), self.c2_row, self.c2_slider, self.c2_wobbler_row, self.wobbler_freq_row, self.wobbler_slider_frequency, ui.create_spacing(10), self.save_pb))
		
		
        self.tabs=ui.create_tabs(self.objective_tab, self.condenser_tab)
		
        self.ui_view=ui.create_column(self.tabs)




        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =gainhandler(instrument, document_controller.event_loop)
        ui_view=gainView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: probe_inst.probeDevice) -> None:
    panel_id = "Probe"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Probe")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
