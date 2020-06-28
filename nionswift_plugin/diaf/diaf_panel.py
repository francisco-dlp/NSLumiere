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

from . import diaf_inst
import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class diafhandler:


    def __init__(self,instrument:diaf_inst.diafDevice,event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.set_full_range_listener=self.instrument.set_full_range.listen(self.total_range_2)

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
    

    def save_ROA(self, widget):	
        panel_dir=os.path.dirname(__file__)
        abs_path=os.path.join(panel_dir, 'diafs_settings.json')	
        with open(abs_path) as savfile:
            json_object=json.load(savfile) #data is load json
        
        json_object['ROA'][self.obj_combo_box.current_item]={"m1": self.m1_slider.value, "m2": self.m2_slider.value}
        json_object['ROA']['last']=self.obj_combo_box.current_index

        with open(abs_path, 'w') as json_file:
            json.dump(json_object, json_file)
        
        self.total_range(widget)

    def save_SA(self, widget):
        panel_dir=os.path.dirname(__file__)
        abs_path=os.path.join(panel_dir, 'diafs_settings.json')	
        with open(abs_path) as savfile:
            json_object=json.load(savfile) #data is load json
        
        json_object['VOA'][self.sa_combo_box.current_item]={"m3": self.m3_slider.value, "m4": self.m4_slider.value}
        json_object['VOA']['last']=self.sa_combo_box.current_index

        with open(abs_path, 'w') as json_file:
            json.dump(json_object, json_file)

        self.total_range(widget)
 
    def total_range_2(self):
        self.m1_slider.maximum=130000
        self.m1_slider.minimum=50000
        
        self.m2_slider.maximum=95000
        self.m2_slider.minimum=75000
        
        self.m3_slider.maximum=140000
        self.m3_slider.minimum=60000
        
        self.m4_slider.maximum=70000
        self.m4_slider.minimum=50000


    def total_range(self, widget):
        self.m1_slider.maximum=130000
        self.m1_slider.minimum=50000
        
        self.m2_slider.maximum=95000
        self.m2_slider.minimum=75000
        
        self.m3_slider.maximum=140000
        self.m3_slider.minimum=60000
        
        self.m4_slider.maximum=70000
        self.m4_slider.minimum=50000

    def slider_release(self, widget):
        widget.maximum=widget.value+2000
        widget.minimum=widget.value-2000



class diafView:


    def __init__(self, instrument:diaf_inst.diafDevice):
        ui = Declarative.DeclarativeUI()
        
        self.full_range_pb=ui.create_push_button(name='full_range_pb', text='Full Range', on_clicked='total_range', width=150)
        self.save_obj_pb = ui.create_push_button(name='save_obj_pb', text='Save Settings', on_clicked='save_ROA', width=150)
        self.save_sa_pb = ui.create_push_button(name='save_sa_pb', text='Save Settings', on_clicked='save_SA', width=150)
	


        self.obj_combo_box=ui.create_combo_box(name='obj_combo_box', items=['None', '50', '100', '150'], current_index='@binding(instrument.roa_change_f)')
        self.m1_slider_label=ui.create_label(name='m1_slider_label', text='@binding(instrument.m1_f)')
        self.m1_slider = ui.create_slider(name='m1_slider', value='@binding(instrument.m1_f)', minimum=50000, maximum=130000, on_slider_released='slider_release')
        self.m2_slider_label=ui.create_label(name='m2_slider_label', text='@binding(instrument.m2_f)')
        self.m2_slider = ui.create_slider(name='m2_slider', value='@binding(instrument.m2_f)', minimum=75000, maximum=95000, on_slider_released='slider_release')
        self.objective_tab = ui.create_tab(label='Objective', content=ui.create_column(self.obj_combo_box, self.m1_slider_label, self.m1_slider, self.m2_slider_label, self.m2_slider, ui.create_row(self.full_range_pb, ui.create_stretch(), self.save_obj_pb)))
		
        self.sa_combo_box=ui.create_combo_box(name='sa_combo_box', items=['None', '50', '100', '150'], current_index='@binding(instrument.voa_change_f)')
        self.m3_slider_label=ui.create_label(name='m3_slider_label', text='@binding(instrument.m3_f)')
        self.m3_slider = ui.create_slider(name='m3_slider', value='@binding(instrument.m3_f)', minimum=60000, maximum=140000, on_slider_released='slider_release')
        self.m4_slider_label=ui.create_label(name='m4_slider_label', text='@binding(instrument.m4_f)')
        self.m4_slider = ui.create_slider(name='m4_slider', value='@binding(instrument.m4_f)', minimum=50000, maximum=70000, on_slider_released='slider_release')

        self.sa_tab = ui.create_tab(label='Selected Area', content=ui.create_column(self.sa_combo_box, self.m3_slider_label, self.m3_slider, self.m4_slider_label, self.m4_slider, ui.create_row(self.full_range_pb, ui.create_stretch(), self.save_sa_pb)))

        self.tabs=ui.create_tabs(self.objective_tab, self.sa_tab)
		
        #self.ui_view = ui.create_column(self.all_tabs, ui.create_spacing(10), self.obj_row, self.obj_slider, ui.create_spacing(50), self.obj_wobbler_row)
        self.ui_view=ui.create_column(self.tabs)

        #self.ui_view=ui.create_column(self.init_pb, self.ui_view1, self.ui_view2, self.ui_view3, self.ui_view4, self.ui_view5, spacing=1)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =diafhandler(instrument, document_controller.event_loop)
        ui_view=diafView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: diaf_inst.diafDevice) -> None:
    panel_id = "Apertures"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("Apertures")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
