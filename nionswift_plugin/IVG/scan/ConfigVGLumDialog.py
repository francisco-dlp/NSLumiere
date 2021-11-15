from nion.ui import Declarative
from nion.utils import Event
from nion.swift.model import HardwareSource
import logging

class Handler:
    def __init__(self):
        self.property_changed_event = Event.Event()
        self.__OrsayScanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
        self.__hadf_pmt = int(self.__OrsayScanInstrument.scan_device.orsayscan.GetPMT(1))
        self.__bf_pmt = int(self.__OrsayScanInstrument.scan_device.orsayscan.GetPMT(0))
        self.__bot_blanker=False
        self.__spim_stop = 0

    @property
    def hadf_gain_pmt(self):
        return self.__hadf_pmt

    @hadf_gain_pmt.setter
    def hadf_gain_pmt(self, value):
        self.__hadf_pmt=value
        self.__OrsayScanInstrument.scan_device.orsayscan.SetPMT(1, value)
        self.property_changed_event.fire("hadf_gain_pmt")

    @property
    def bf_gain_pmt(self):
        return self.__bf_pmt

    @bf_gain_pmt.setter
    def bf_gain_pmt(self, value):
        self.__bf_pmt=value
        self.__OrsayScanInstrument.scan_device.orsayscan.SetPMT(0, value)
        self.property_changed_event.fire("bf_gain_pmt")

    @property
    def bottom_blanker(self):
        return self.__bot_blanker

    @bottom_blanker.setter
    def bottom_blanker(self, value):
        self.__bot_blanker = value
        if self.__bot_blanker:
            self.__OrsayScanInstrument.scan_device.orsayscan.SetBottomBlanking(2, 7)
            #self.__OrsayScanInstrument.scan_device.orsayscan.SetTdcLine(1, 2, 7) # Copy Line Start
            #self.__OrsayScanInstrument.scan_device.orsayscan.SetTdcLine(1, 2, 13) #Copy Line 05
        else:
            self.__OrsayScanInstrument.scan_device.orsayscan.SetBottomBlanking(0, 0)

    @property
    def spim_stop(self):
        return str(self.__OrsayScanInstrument.scan_device._Device__tpx3_frameStop)

    @spim_stop.setter
    def spim_stop(self, value):
        try:
            self.__OrsayScanInstrument.scan_device._Device__tpx3_frameStop = int(value)
        except ValueError:
            logging.info(f'***SCAN Dialog***: Please set it as an integer.')

class View():
    def __init__(self):
        ui = Declarative.DeclarativeUI()
        self.hadf_label = ui.create_label(name='hadf_gain', text="HADF Gain")
        self.hadf_gain_slider=ui.create_slider(name='hadf_gain_slider', value='@binding(hadf_gain_pmt)', minimum=0,
                                               maximum=2500)
        self.bf_label = ui.create_label(name='BF_gain', text="BF Gain")
        self.bf_gain_slider=ui.create_slider(name='bf_gain_slider', value='@binding(bf_gain_pmt)', minimum=0,
                                             maximum=2500)
        self.bot_blanker_check_box = ui.create_check_box(name='bot_blanker_check_box', text='Botton Blanker EELS',
                                                         checked='@binding(bottom_blanker)')
        self.spim_stop_label = ui.create_label(name='spim_stop_label', text='SPIM Frame Stop: ')
        self.spim_stop_line_edit = ui.create_line_edit(name='spim_stop_line_edit', text='@binding(spim_stop)', width=50)
        self.spim_row = ui.create_row(self.spim_stop_label, self.spim_stop_line_edit, ui.create_stretch())
        self.column = ui.create_column(self.hadf_label, self.hadf_gain_slider, ui.create_spacing(25), self.bf_label,
                                       self.bf_gain_slider, self.bot_blanker_check_box, ui.create_spacing(25), self.spim_row)
        self.dialog = ui.create_modeless_dialog(self.column, title="Scan Settings")


class ConfigDialog:
    def __init__(self, document_controller):
        # document_controller_ui AND document_controller should be passed to the construct....
        self.widget = Declarative.construct(document_controller.ui, document_controller, View().dialog, Handler())
        if self.widget != None:
            self.widget.show()
