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

from . import ivg_inst
import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class ivghandler:


    def __init__(self,instrument:ivg_inst.ivgDevice,event_loop):

        self.event_loop=event_loop
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
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
        self.event_loop.create_task(self.do_enable(True, []))

    def prepare_widget_disable(self,value):
        self.event_loop.create_task(self.do_enable(False, []))
    


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
        self.LL_row=ui.create_row(self.LL_label, self.LL_vac, ui.create_stretch())

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

        
        self.voa_label=ui.create_label(name='voa_label', text='VOA: ')
        self.voa_value=ui.create_label(name='voa_value', text='@binding(instrument.voa_val_f)')
        self.voa_row=ui.create_row(self.voa_label, self.voa_value, ui.create_stretch())

        self.roa_label=ui.create_label(name='roa_label', text='ROA: ')
        self.roa_value=ui.create_label(name='roa_value', text='@binding(instrument.roa_val_f)')
        self.roa_row=ui.create_row(self.roa_label, self.roa_value, ui.create_stretch())

        self.aper_group=ui.create_group(title='Apertures: ', content=ui.create_column(self.voa_row, self.roa_row))
        
        self.ui_view=ui.create_column(self.EHT_row, self.vac_group, self.obj_group, self.aper_group, spacing=5)



        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =ivghandler(instrument, document_controller.event_loop)
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
