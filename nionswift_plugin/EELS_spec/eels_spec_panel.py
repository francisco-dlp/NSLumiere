# standard libraries
import gettext

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

from . import eels_spec_inst


import logging
_ = gettext.gettext
from nion.utils import Model



import inspect


class eels_spec_handler:


    def __init__(self,instrument:eels_spec_inst.EELS_SPEC_Device,event_loop):

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
    



class eels_spec_View:


    def __init__(self, instrument:eels_spec_inst.EELS_SPEC_Device):
        ui = Declarative.DeclarativeUI()
		
        self.fx_label = ui.create_label(text='FX:', name='fx_label')
        self.fx_value = ui.create_line_edit(name='fx_value', text='@binding(instrument.fx_'+'edit_f)')
        self.fx_row = ui.create_row(self.fx_label, self.fx_value)
        self.fx_slider = ui.create_slider(name='fx_slider', value='@binding(instrument.fx_slider_f)', minimum=-32767, maximum=32767)

        self.fy_label = ui.create_label(text='FY:', name='fy_label')
        self.fy_value = ui.create_line_edit(name='fy_value', text='@binding(instrument.fy_edit_f)')
        self.fy_row = ui.create_row(self.fy_label, self.fy_value)
        self.fy_slider = ui.create_slider(name='fy_slider', value='@binding(instrument.fy_slider_f)', minimum=-32767, maximum=32767)
        
        self.sx_label = ui.create_label(text='SX:', name='sx_label')
        self.sx_value = ui.create_line_edit(name='sx_value', text='@binding(instrument.sx_edit_f)')
        self.sx_row = ui.create_row(self.sx_label, self.sx_value)
        self.sx_slider = ui.create_slider(name='sx_slider', value='@binding(instrument.sx_slider_f)', minimum=-32767, maximum=32767)
        
        self.sy_label = ui.create_label(text='SY:', name='sy_label')
        self.sy_value = ui.create_line_edit(name='sy_value', text='@binding(instrument.sy_edit_f)')
        self.sy_row = ui.create_row(self.sy_label, self.sy_value)
        self.sy_slider = ui.create_slider(name='sy_slider', value='@binding(instrument.sy_slider_f)', minimum=-32767, maximum=32767)		

        self.dy_label = ui.create_label(text='DY:', name='dy_label')
        self.dy_value = ui.create_line_edit(name='dy_value', text='@binding(instrument.dy_edit_f)')
        self.dy_row = ui.create_row(self.dy_label, self.dy_value)
        self.dy_slider = ui.create_slider(name='dy_slider', value='@binding(instrument.dy_slider_f)', minimum=-32767, maximum=32767)
	
        self.focus_tab = ui.create_tab(label='Focus', content=ui.create_column(ui.create_spacing(10),\
        self.fx_row, self.fx_slider, ui.create_spacing(50),\
        self.fy_row, self.fy_slider, ui.create_spacing(50),\
        self.sx_row, self.sx_slider, ui.create_spacing(50),\
        self.sy_row, self.sy_slider, ui.create_spacing(50),\
        self.dy_row, self.dy_slider, ui.create_spacing(50)))
		
		
        self.q1_label = ui.create_label(text='Q1:', name='q1_label')
        self.q1_value = ui.create_line_edit(name='q1_value', text='@binding(instrument.q1_edit_f)')
        self.q1_row = ui.create_row(self.q1_label, self.q1_value)
        self.q1_slider = ui.create_slider(name='q1_slider', value='@binding(instrument.q1_slider_f)', minimum=-32767, maximum=32767)

        self.q2_label = ui.create_label(text='Q2:', name='q2_label')
        self.q2_value = ui.create_line_edit(name='q2_value', text='@binding(instrument.q2_edit_f)')
        self.q2_row = ui.create_row(self.q2_label, self.q2_value)
        self.q2_slider = ui.create_slider(name='q2_slider', value='@binding(instrument.q2_slider_f)', minimum=-32767, maximum=32767)
        
        self.q3_label = ui.create_label(text='Q3:', name='q3_label')
        self.q3_value = ui.create_line_edit(name='q3_value', text='@binding(instrument.q3_edit_f)')
        self.q3_row = ui.create_row(self.q3_label, self.q3_value)
        self.q3_slider = ui.create_slider(name='q3_slider', value='@binding(instrument.q3_slider_f)', minimum=-32767, maximum=32767)
        
        self.q4_label = ui.create_label(text='Q4:', name='q4_label')
        self.q4_value = ui.create_line_edit(name='q4_value', text='@binding(instrument.q4_edit_f)')
        self.q4_row = ui.create_row(self.q4_label, self.q4_value)
        self.q4_slider = ui.create_slider(name='q4_slider', value='@binding(instrument.q4_slider_f)', minimum=-32767, maximum=32767)		

        self.dx_label = ui.create_label(text='DX:', name='dx_label')
        self.dx_value = ui.create_line_edit(name='dx_value', text='@binding(instrument.dx_edit_f)')
        self.dx_row = ui.create_row(self.dx_label, self.dx_value)
        self.dx_slider = ui.create_slider(name='dx_slider', value='@binding(instrument.dx_slider_f)', minimum=-32767, maximum=32767)
		
        self.dmx_label = ui.create_label(text='DMX:', name='dmx_label')
        self.dmx_value = ui.create_line_edit(name='dmx_value', text='@binding(instrument.dmx_edit_f)')
        self.dmx_row = ui.create_row(self.dmx_label, self.dmx_value)
        self.dmx_slider = ui.create_slider(name='dmx_slider', value='@binding(instrument.dmx_slider_f)', minimum=-32767, maximum=32767)		
        
        self.dispersion_tab = ui.create_tab(label='Dispersion', content=ui.create_column(ui.create_spacing(10),\
        self.q1_row, self.q1_slider, ui.create_spacing(50),\
        self.q2_row, self.q2_slider, ui.create_spacing(50),\
        self.q3_row, self.q3_slider, ui.create_spacing(50),\
        self.q4_row, self.q4_slider, ui.create_spacing(50),\
        self.dx_row, self.dx_slider, ui.create_spacing(50),\
        self.dmx_row, self.dmx_slider, ui.create_spacing(50)))		
		
        self.tabs=ui.create_tabs(self.focus_tab, self.dispersion_tab)
		
        self.ui_view=ui.create_column(self.tabs)

        
def create_spectro_panel(document_controller, panel_id, properties):
        instrument = properties["instrument"]
        ui_handler =eels_spec_handler(instrument, document_controller.event_loop)
        ui_view=eels_spec_View(instrument)
        panel = Panel.Panel(document_controller, panel_id, properties)

        finishes = list()
        panel.widget = Declarative.construct(document_controller.ui, None, ui_view.ui_view, ui_handler, finishes)


        for finish in finishes:
            finish()
        if ui_handler and hasattr(ui_handler, "init_handler"):
            ui_handler.init_handler()
        return panel


def run(instrument: eels_spec_inst.EELS_SPEC_Device) -> None:
    panel_id = "EELS Spectrometer"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("EELS Spectrometer")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
