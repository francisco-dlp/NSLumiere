# standard libraries
import gettext
import os
import json
import numpy

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

from . import ivg_inst
import logging
_ = gettext.gettext
from nion.utils import Model
from nion.swift.model import DataItem
from nion.swift.model import DocumentModel


import inspect

class dataItemCreation():
    def __init__(self, title, array):
        self.data_item=DataItem.DataItem()
        self.data_item.define_property("title", title)
        self.data_item.set_data(array)



class ivghandler:


    def __init__(self,instrument:ivg_inst.ivgDevice, document_controller):

        self.event_loop=document_controller.event_loop
        self.document_controller=document_controller
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.append_data_listener=self.instrument.append_data.listen(self.append_data)
        self.stop_append_data_listener = self.instrument.stop_append_data.listen(self.stop_append_data)



        self.ll_array = numpy.zeros(100)
        self.gun_array = numpy.zeros(100)
        self.obj_array = numpy.zeros(100)
        self.ll_di = dataItemCreation("AirLock Vacuum", self.ll_array)
        self.gun_di = dataItemCreation("Gun Vacuum", self.gun_array)
        self.obj_di = dataItemCreation("Objective Temperature", self.obj_array)
        
        self.document_controller.document_model.append_data_item(self.ll_di.data_item)
        self.document_controller.document_model.append_data_item(self.gun_di.data_item)
        self.document_controller.document_model.append_data_item(self.obj_di.data_item)

        #self.LL_array=numpy.zeros(1000)
        #self.LL_data_item = DataItem.DataItem()
        #self.LL_data_item.define_property("title", "LL_Vacuum")
        #self.LL
        #self.LL_data_item.set_data(self.np_array)
        #self.document_controler.document_model.append_data_item(self.LL_data_item)


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


    def append_data(self, value, index):
        self.ll_array[index], self.gun_array[index], self.obj_array[index]= value
        
        self.obj_di.data_item._enter_live_state()
        self.gun_di.data_item._enter_live_state()
        self.ll_di.data_item._enter_live_state()
        
        self.obj_di.data_item.set_data(self.obj_array)
        self.gun_di.data_item.set_data(self.gun_array)
        self.ll_di.data_item.set_data(self.ll_array)
        

    def stop_append_data(self):
        if self.obj_di.data_item.is_live: self.obj_di.data_item._exit_live_state()
        if self.ll_di.data_item.is_live: self.ll_di.data_item._exit_live_state()
        if self.gun_di.data_item.is_live: self.gun_di.data_item._exit_live_state()


    


class ivgView:


    def __init__(self, instrument:ivg_inst.ivgDevice):
        ui = Declarative.DeclarativeUI()
        
        self.EHT_label=ui.create_label(name='EHT_label', text='HT: ')
        self.EHT_combo_box=ui.create_combo_box(name='EHT_combo_box', items=['40', '60', '80', '100'], current_index='@binding(instrument.EHT_f)')
        self.EHT_row=ui.create_row(self.EHT_label, self.EHT_combo_box, ui.create_stretch())

        self.gun_label=ui.create_label(name='gun_label', text='Gun Vacuum: ')
        self.gun_vac=ui.create_label(name='gun_vac', text='@binding(instrument.gun_vac_f)')
        self.gun_row=ui.create_row(self.gun_label, self.gun_vac, ui.create_stretch())


        self.LL_label=ui.create_label(name='LL_label', text='AirLock Vacuum: ')
        self.LL_vac=ui.create_label(name='LL_vac', text='@binding(instrument.LL_vac_f)')
        self.LL_plot=ui.create_check_box(name='LL_plot', text='Monitor', checked='@binding(instrument.LL_mon_f)')
        self.LL_row=ui.create_row(self.LL_label, self.LL_vac, ui.create_spacing(10), self.LL_plot, ui.create_stretch())

        self.vac_group=ui.create_group(title='Gauges: ', content=ui.create_column(self.gun_row, self.LL_row))

        self.obj_cur=ui.create_label(name='obj_cur', text='Current: ')
        self.obj_cur_value=ui.create_label(name='obj_cur_value', text='@binding(instrument.obj_cur_f)')
        self.obj_cur_row=ui.create_row(self.obj_cur, self.obj_cur_value, ui.create_stretch())
        
        self.obj_vol=ui.create_label(name='obj_vol', text='Voltage: ')
        self.obj_vol_value=ui.create_label(name='obj_vol_value', text='@binding(instrument.obj_vol_f)')
        self.obj_vol_row=ui.create_row(self.obj_vol, self.obj_vol_value, ui.create_stretch())
        
        self.obj_temp=ui.create_label(name='obj_temp', text='Temperature: ')
        self.obj_temp_value=ui.create_label(name='obj_temp_value', text='@binding(instrument.obj_temp_f)')
        self.obj_temp_row=ui.create_row(self.obj_temp, self.obj_temp_value, ui.create_stretch())
        
        self.obj_group=ui.create_group(title='Objective Lens: ', content=ui.create_column(self.obj_cur_row, self.obj_vol_row, self.obj_temp_row))

        self.c1_cur=ui.create_label(name='c1_cur', text='C1: ')
        self.c1_cur_value=ui.create_label(name='c1_cur_value', text='@binding(instrument.c1_cur_f)')
        self.c1_vol=ui.create_label(name='c1_vol', text='V1: ')
        self.c1_vol_value=ui.create_label(name='c1_vol_value', text='@binding(instrument.c1_vol_f)')
        self.c1_res=ui.create_label(name='c1_res', text='Ω1: ')
        self.c1_res_value=ui.create_label(name='c1_res_value', text='@binding(instrument.c1_res_f)')
        self.c1_res_row=ui.create_row(self.c1_cur, self.c1_cur_value, ui.create_spacing(10), self.c1_vol, self.c1_vol_value, ui.create_spacing(10), self.c1_res, self.c1_res_value, ui.create_stretch())

        self.c2_cur=ui.create_label(name='c2_cur', text='C2: ')
        self.c2_cur_value=ui.create_label(name='c2_cur_value', text='@binding(instrument.c2_cur_f)')
        self.c2_vol=ui.create_label(name='c2_vol', text='V2: ')
        self.c2_vol_value=ui.create_label(name='c2_vol_value', text='@binding(instrument.c2_vol_f)')
        self.c2_res=ui.create_label(name='c2_res', text='Ω2: ')
        self.c2_res_value=ui.create_label(name='c2_res_value', text='@binding(instrument.c2_res_f)')
        self.c2_res_row=ui.create_row(self.c2_cur, self.c2_cur_value, ui.create_spacing(10), self.c2_vol, self.c2_vol_value, ui.create_spacing(10), self.c2_res, self.c2_res_value, ui.create_stretch())

        self.cond_group=ui.create_group(title='Condenser Lens: ', content=ui.create_column(self.c1_res_row, self.c2_res_row))

        
        self.voa_label=ui.create_label(name='voa_label', text='VOA: ')
        self.voa_value=ui.create_label(name='voa_value', text='@binding(instrument.voa_val_f)')
        self.voa_row=ui.create_row(self.voa_label, self.voa_value, ui.create_stretch())

        self.roa_label=ui.create_label(name='roa_label', text='ROA: ')
        self.roa_value=ui.create_label(name='roa_value', text='@binding(instrument.roa_val_f)')
        self.roa_row=ui.create_row(self.roa_label, self.roa_value, ui.create_stretch())

        self.aper_group=ui.create_group(title='Apertures: ', content=ui.create_column(self.voa_row, self.roa_row))
        
        self.ui_view=ui.create_column(self.EHT_row, self.vac_group, self.obj_group, self.cond_group, self.aper_group, spacing=5)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =ivghandler(instrument, document_controller)
        ui_view=ivgView(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: ivg_inst.ivgDevice) -> None:
    panel_id = "IVG"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("VG Lumiere - Status")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
