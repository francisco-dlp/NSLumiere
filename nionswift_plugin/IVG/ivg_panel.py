# standard libraries
import gettext
import numpy

from nion.swift import Panel
from nion.swift import Workspace
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.ui import Declarative
from nion.ui import UserInterface
from nion.swift.model import DataItem
from nion.swift.model import Utility

from . import ivg_inst

_ = gettext.gettext


MAX_PTS = 5000
STAGE_MATRIX_SIZE = 210

class dataItemCreation():
    def __init__(self, title, array, which):
        
        self.timezone = Utility.get_local_timezone()
        self.timezone_offset = Utility.TimezoneMinutesToStringConverter().convert(Utility.local_utcoffset_minutes())
            
        self.calibration=Calibration.Calibration()

        if which!='STA':
            self.dimensional_calibrations = [Calibration.Calibration()]
            if which=='OBJ':
                self.calibration.units = 'ºC'
                self.dimensional_calibrations[0].units='min'
                self.dimensional_calibrations[0].scale=1/60.
            if which=='LL':
                self.calibration.units='mBar'
                self.dimensional_calibrations[0].units='min'
                self.dimensional_calibrations[0].scale=1/60.
            if which=='GUN':
                self.calibration.units='mTor'
                self.dimensional_calibrations[0].units='min'
                self.dimensional_calibrations[0].scale=1/60.
            self.xdata=DataAndMetadata.new_data_and_metadata(array, self.calibration, self.dimensional_calibrations, timezone=self.timezone, timezone_offset=self.timezone_offset)
        else:
            self.calibration.units=''
            
            self.dim_calib01 = Calibration.Calibration()
            self.dim_calib02 = Calibration.Calibration()

            self.dim_calib01.units='µm'
            self.dim_calib01.scale=-1600/STAGE_MATRIX_SIZE
            self.dim_calib01.offset=800
            self.dim_calib02.units='µm'
            self.dim_calib02.scale=1600/STAGE_MATRIX_SIZE
            self.dim_calib02.offset=-800
            
            self.dimensional_calibrations=[self.dim_calib01, self.dim_calib02]
            
            self.xdata=DataAndMetadata.new_data_and_metadata(array, self.calibration, self.dimensional_calibrations, timezone=self.timezone, timezone_offset=self.timezone_offset)
            
        
        
        self.data_item=DataItem.DataItem()
        self.data_item.set_xdata(self.xdata)
        self.data_item.title = title
        self.data_item._enter_live_state()

    async def update_data_only(self, array: numpy.array):
        self.xdata=DataAndMetadata.new_data_and_metadata(array, self.calibration, self.dimensional_calibrations, timezone=self.timezone, timezone_offset=self.timezone_offset)
        self.data_item.set_xdata(self.xdata)

    def fast_update_data_only(self, array: numpy.array):
        self.data_item.set_data(array)


class ivghandler:

    def __init__(self,instrument:ivg_inst.ivgInstrument, document_controller):

        self.event_loop=document_controller.event_loop
        self.document_controller=document_controller
        self.instrument=instrument
        self.enabled = False
        self.property_changed_event_listener=self.instrument.property_changed_event.listen(self.prepare_widget_enable)
        self.busy_event_listener=self.instrument.busy_event.listen(self.prepare_widget_disable)
        self.append_data_listener=self.instrument.append_data.listen(self.append_data)
        self.stage_event_listener=self.instrument.stage_event.listen(self.stage_data)

        self.ll_array = numpy.zeros(MAX_PTS) #air lock (or load lock) gauge
        self.gun_array = numpy.zeros(MAX_PTS) #gun gauge
        self.obj_array = numpy.zeros(MAX_PTS) #objective lens temperature
        self.stage_array = numpy.zeros((STAGE_MATRIX_SIZE, STAGE_MATRIX_SIZE)) #stage tracker

        self.ll_di=None
        self.gun_di=None
        self.obj_di=None
        self.stage_di=None
        
    def init_handler(self):
        self.instrument.init_handler()

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

    def stage_data(self, stage1, stage2):
        index1 = int(round(STAGE_MATRIX_SIZE/2-stage1*1e6/(2100/STAGE_MATRIX_SIZE)))
        index2 = int(round(stage2*1e6/(2100/STAGE_MATRIX_SIZE)-STAGE_MATRIX_SIZE/2))
        if abs(index1)<STAGE_MATRIX_SIZE and abs(index2)<STAGE_MATRIX_SIZE:
            if self.stage_array[index1][index2]<=100:
                self.stage_array[index1][index2] += 5

        if self.stage_di:
            self.event_loop.create_task(self.stage_di.update_data_only(self.stage_array))

    def append_data(self, value, index):
        self.ll_array[index], self.gun_array[index], self.obj_array[index] = value

        if self.ll_di:
            self.event_loop.create_task(self.ll_di.update_data_only(self.ll_array))
        if self.gun_di:
            self.event_loop.create_task(self.gun_di.update_data_only(self.gun_array))
        if self.obj_di:
            self.event_loop.create_task(self.obj_di.update_data_only(self.obj_array))

    async def data_item_show(self, DI):
        self.document_controller.document_model.append_data_item(DI)

    async def data_item_remove(self, DI):
        self.document_controller.document_model.remove_data_item(DI)

    async def data_item_exit_live(self, DI):
        DI._exit_live_state()

    def monitor_air_lock(self, widget):
        self.ll_di = dataItemCreation("AirLock Vacuum", self.ll_array, 'LL')
        self.event_loop.create_task(self.data_item_show(self.ll_di.data_item))

    def monitor_gun(self, widget):
        self.gun_di = dataItemCreation("Gun Vacuum", self.gun_array, 'GUN')
        self.event_loop.create_task(self.data_item_show(self.gun_di.data_item))

    def monitor_obj_temp(self, widget):
        self.obj_di = dataItemCreation("Objective Temperature", self.obj_array, 'OBJ')
        self.event_loop.create_task(self.data_item_show(self.obj_di.data_item))

    def monitor_stage(self, widget):
        self.stage_di = dataItemCreation("Stage Position", self.stage_array, 'STA')
        self.event_loop.create_task(self.data_item_show(self.stage_di.data_item))

    def clear_stage(self, widget):
        self.stage_array = numpy.zeros((STAGE_MATRIX_SIZE, STAGE_MATRIX_SIZE))

class ivgView:


    def __init__(self, instrument:ivg_inst.ivgInstrument):
        ui = Declarative.DeclarativeUI()
        
        self.EHT_label=ui.create_label(name='EHT_label', text='HT: ')
        self.EHT_combo_box=ui.create_combo_box(name='EHT_combo_box', items=['40', '60', '80', '100'], current_index='@binding(instrument.EHT_f)')

        self.stand_label = ui.create_label(name='stand_label', text='Stand By:')
        self.stand_value=ui.create_check_box(name='stand_value', checked='@binding(instrument.stand_f)')

        self.thread_counter = ui.create_label(name='thread_coubter', text='# Threads: ')
        self.thread_counter_value = ui.create_label(name='thread_counter_value', text='@binding(instrument.thread_cts_f)')

        self.EHT_row=ui.create_row(self.EHT_label, self.EHT_combo_box, ui.create_spacing(25), self.stand_label, self.stand_value, ui.create_stretch(),
                                   self.thread_counter, self.thread_counter_value)

        self.gun_label=ui.create_label(name='gun_label', text='Gun Vacuum: ')
        self.gun_vac=ui.create_label(name='gun_vac', text='@binding(instrument.gun_vac_f)')
        self.gun_pb=ui.create_push_button(name='gun_pb', text='Monitor', on_clicked='monitor_gun', width=100)
        self.gun_row=ui.create_row(self.gun_label, self.gun_vac, ui.create_stretch(), self.gun_pb)


        self.LL_label=ui.create_label(name='LL_label', text='AirLock Vacuum: ')
        self.LL_vac=ui.create_label(name='LL_vac', text='@binding(instrument.LL_vac_f)')
        self.LL_pb=ui.create_push_button(name='LL_pb', text='Monitor', on_clicked='monitor_air_lock', width=100)
        self.LL_row=ui.create_row(self.LL_label, self.LL_vac, ui.create_stretch(), self.LL_pb)

        self.vac_group=ui.create_group(title='Gauges: ', content=ui.create_column(self.gun_row, self.LL_row))

        self.obj_cur=ui.create_label(name='obj_cur', text='Current: ')
        self.obj_cur_value=ui.create_label(name='obj_cur_value', text='@binding(instrument.obj_cur_f)')
        self.obj_cur_row=ui.create_row(self.obj_cur, self.obj_cur_value, ui.create_stretch())
        
        self.obj_vol=ui.create_label(name='obj_vol', text='Voltage: ')
        self.obj_vol_value=ui.create_label(name='obj_vol_value', text='@binding(instrument.obj_vol_f)')
        self.obj_vol_row=ui.create_row(self.obj_vol, self.obj_vol_value, ui.create_stretch())
        
        self.obj_temp=ui.create_label(name='obj_temp', text='Temperature: ')
        self.obj_temp_value=ui.create_label(name='obj_temp_value', text='@binding(instrument.obj_temp_f)')
        self.obj_pb=ui.create_push_button(name='obj_pb', text='Monitor', on_clicked='monitor_obj_temp', width=100)
        self.obj_temp_row=ui.create_row(self.obj_temp, self.obj_temp_value, ui.create_stretch(), self.obj_pb)
        
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


        self.x_stage_label=ui.create_label(name='x_stage_label', text='Motor X (μm): ')
        self.x_stage_real=ui.create_label(name='x_stage_real', text='@binding(instrument.x_stage_f)')
        self.x_stage_edit = ui.create_line_edit(name='x_stage_edit', text='@binding(instrument.x_stage_f)', width='50')
        self.stage_pb=ui.create_push_button(name='stage_pb', text='Monitor', on_clicked='monitor_stage', width=100)
        self.x_stage_row = ui.create_row(self.x_stage_label, self.x_stage_real, ui.create_spacing(10), self.x_stage_edit, ui.create_stretch(), self.stage_pb)

        self.y_stage_label=ui.create_label(name='y_stage_label', text='Motor Y (μm): ')
        self.y_stage_real=ui.create_label(name='y_stage_real', text='@binding(instrument.y_stage_f)')
        self.y_stage_edit = ui.create_line_edit(name='y_stage_edit', text='@binding(instrument.y_stage_f)', width='50')
        self.stage_clear_pb=ui.create_push_button(name='stage_clear_pb', text='Clear Track', on_clicked='clear_stage', width=100)
        self.y_stage_row = ui.create_row(self.y_stage_label, self.y_stage_real, ui.create_spacing(10), self.y_stage_edit, ui.create_stretch(), self.stage_clear_pb)

        self.stage_group=ui.create_group(title='VG Stage', content=ui.create_column(self.x_stage_row, self.y_stage_row))
        
        self.ui_view=ui.create_column(self.EHT_row, self.vac_group, self.obj_group, self.cond_group, self.aper_group, self.stage_group, spacing=5)


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


def run(instrument: ivg_inst.ivgInstrument) -> None:
    panel_id = "IVG"#make sure it is unique, otherwise only one of the panel will be displayed
    name = _("VG - Status")
    Workspace.WorkspaceManager().register_panel(create_spectro_panel, panel_id, name, ["left", "right"], "left",
                                                {"instrument": instrument})
