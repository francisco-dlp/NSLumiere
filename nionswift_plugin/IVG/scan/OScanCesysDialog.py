from nion.ui import Declarative
from nion.utils import Event
from nion.swift.model import HardwareSource

ACQUISITION_WINDOW = ['boxcar', 'triang', 'blackman', 'hamming', 'hann']
KERNEL_LIST = ['None', 'Square', 'Triangular', 'Gaussian', 'Blackman', 'Custom', 'First pixel', 'Last pixel', 'Given pixel']
SCAN_MODES = ['Normal', 'Serpentine', 'Random', 'Mini-scans', 'Lissajous', 'Sawtooth Lissajous']
IMAGE_VIEW_MODES = ['Normal', 'Ordered', 'DAC-based', 'Low-pass filter', 'Inpainting']
ADC_READOUT_MODES = ['FIR', 'Pixel counter', 'IIR', 'Multip.', 'Kernel', 'Fixed TAP']

def function_creator(name: str):
    def func(self):
        return getattr(self.scan, name)
    def func2(self, value):
        return setattr(self.scan, name, value)
    return func, func2

class Handler:
    def __init__(self):
        self.property_changed_event = Event.Event()
        scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("open_scan_device")
        self.scan = scan.scan_device.scan_engine

    f1, f2 = function_creator("imagedisplay")
    imagedisplay = property(f1, f2)
    f1, f2 = function_creator("imagedisplay_filter_intensity")
    imagedisplay_filter_intensity = property(f1, f2)
    f1, f2 = function_creator("flyback_us")
    flyback_us = property(f1, f2)
    f1, f2 = function_creator("kernel_mode")
    kernel_mode = property(f1, f2)
    f1, f2 = function_creator("given_pixel")
    given_pixel = property(f1, f2)
    f1, f2 = function_creator("dsp_filter")
    dsp_filter = property(f1, f2)
    f1, f2 = function_creator("video_delay")
    video_delay = property(f1, f2)
    f1, f2 = function_creator("pause_sampling")
    pause_sampling = property(f1, f2)
    f1, f2 = function_creator("adc_acquisition_mode")
    adc_acquisition_mode = property(f1, f2)
    f1, f2 = function_creator("acquisition_cutoff")
    acquisition_cutoff = property(f1, f2)
    f1, f2 = function_creator("acquisition_window")
    acquisition_window = property(f1, f2)
    f1, f2 = function_creator("rastering_mode")
    rastering_mode = property(f1, f2)
    f1, f2 = function_creator("mini_scan")
    mini_scan = property(f1, f2)
    f1, f2 = function_creator("lissajous_nx")
    lissajous_nx = property(f1, f2)
    f1, f2 = function_creator("lissajous_ny")
    lissajous_ny = property(f1, f2)
    f1, f2 = function_creator("lissajous_phase")
    lissajous_phase = property(f1, f2)
    f1, f2 = function_creator("external_trigger")
    external_trigger = property(f1, f2)
    f1, f2 = function_creator("magboard_switches")
    magboard_switches = property(f1, f2)
    f1, f2 = function_creator("offset_adc")
    offset_adc = property(f1, f2)
    f1, f2 = function_creator("duty_cycle")
    duty_cycle = property(f1, f2)

class View():
    def __init__(self):
        ui = Declarative.DeclarativeUI()
        #Acquisition parameters
        self.imageshow_text = ui.create_label(name='imageshow_text', text="Image display: ")
        self.imageshow_value = ui.create_combo_box(
            items=IMAGE_VIEW_MODES,
            current_index='@binding(imagedisplay)',
            name='rastering_value', width='100')
        self.image_filter_intensity_text = ui.create_label(name='image_filter_intensity_text', text='Filter intensity: ')
        self.image_filter_intensity_value = ui.create_line_edit(name='image_filter_intensity_value', text='@binding(imagedisplay_filter_intensity)')
        self.imageshow_row = ui.create_row(self.imageshow_text, self.imageshow_value, ui.create_spacing(10),
                                           self.image_filter_intensity_text, self.image_filter_intensity_value,
                                           ui.create_stretch())

        self.acquisition_parameters_group = ui.create_group(title='Acquisition parameters', content=ui.create_column(
            self.imageshow_row
        ))

        #Rastering parameters
        self.flyback_text = ui.create_label(name='flyback_text', text="Flyback value (us): ")
        self.flyback_value = ui.create_line_edit(name='flyback_value', text='@binding(flyback_us)')
        self.flyback_row = ui.create_row(self.flyback_text, self.flyback_value, ui.create_stretch())

        self.external_trigger_text = ui.create_label(name='external_trigger_text', text="External Trigger: ")
        self.external_trigger = ui.create_check_box(name='external_trigger', checked='@binding(external_trigger)')
        self.external_trigger_row = ui.create_row(self.external_trigger_text, self.external_trigger,
                                                  ui.create_stretch())

        self.rastering_text = ui.create_label(name='rastering_text', text="Rastering mode: ")
        self.rastering_value = ui.create_combo_box(items=SCAN_MODES,
                                                   current_index='@binding(rastering_mode)',
                                                   name='rastering_value', width='100')
        self.mini_scan_text = ui.create_label(name='mini_scan_text', text="Mini-scans: ")
        self.mini_scan_value = ui.create_line_edit(name='mini_scan_value', text='@binding(mini_scan)', width='100')
        self.rastering_row = ui.create_row(self.rastering_text, self.rastering_value, ui.create_stretch(),
                                           self.mini_scan_text, self.mini_scan_value)

        self.lissajous_nx_text = ui.create_label(name='lissajous_text', text="Liss. X (Hz): ")
        self.lissajous_nx_value = ui.create_line_edit(name='lissajous_value: ', width=45, text='@binding(lissajous_nx)')
        self.lissajous_ny_text = ui.create_label(name='lissajous_text', text="Liss. Y: (Hz) ")
        self.lissajous_ny_value = ui.create_line_edit(name='lissajous_value: ', width=45, text='@binding(lissajous_ny)')
        self.lissajous_phase_text = ui.create_label(name='lissajous_phase_text', text="Lissajous phase: ")
        self.lissajous_phase_value = ui.create_line_edit(name='lissajous_phase_value: ', width=30,
                                                         text='@binding(lissajous_phase)')
        self.lissajous_row = ui.create_row(self.lissajous_nx_text, self.lissajous_nx_value, ui.create_spacing(5),
                                           self.lissajous_ny_text, self.lissajous_ny_value, ui.create_spacing(5),
                                           self.lissajous_phase_text, self.lissajous_phase_value,
                                           ui.create_stretch())

        self.rastering_group = ui.create_group(title='Scanning parameters', content=ui.create_column(
            self.flyback_row, self.rastering_row, self.lissajous_row
        ))
        #ADC parameters

        self.kernel_mode_text = ui.create_label(name='kernel_mode_text', text="DSP Kernel: ")
        self.kernel_mode_value = ui.create_combo_box(items=KERNEL_LIST,
                                                current_index='@binding(kernel_mode)',
                                                name='kernel_mode_value', width='100')
        self.kernel_given_pixel_label = ui.create_label(text='Given pixel: ')
        self.kernel_given_pixel_value = ui.create_line_edit(name='kernel_given_pixel_value',
                                                            text='@binding(given_pixel)', width=45)
        self.kernel_mode_row = ui.create_row(self.kernel_mode_text, self.kernel_mode_value, ui.create_stretch(),
                                             self.kernel_given_pixel_label, self.kernel_given_pixel_value)

        self.filter_text = ui.create_label(name='filter_text', text="IIR Filter: ")
        self.filter_value = ui.create_combo_box(items=['1', '2', '4', '8', '16', '32', '64'],
                                                current_index='@binding(dsp_filter)',
                                                name='filter_value', width = '100')
        self.filter_row = ui.create_row(self.filter_text, self.filter_value, ui.create_stretch())

        self.video_delay_text = ui.create_label(name='video_delay_text', text="Video delay: ")
        self.video_delay_value = ui.create_line_edit(text='@binding(video_delay)',
                                                name='video_delay_value', width='100')
        self.enable_pause_sampling = ui.create_check_box(name='enable_pause_sampling', text="Pause Sampling", checked='@binding(pause_sampling)')
        self.video_delay_row = ui.create_row(self.video_delay_text, self.video_delay_value, ui.create_stretch(), self.enable_pause_sampling)

        self.acqusition_adc_text = ui.create_label(name='acqusition_adc_text', text="ADC type: ")
        self.acquisition_adc_value = ui.create_combo_box(items=ADC_READOUT_MODES,
                                                current_index='@binding(adc_acquisition_mode)',
                                                name='acquisition_adc_value', width='100')
        self.duty_cycle_label = ui.create_label(name='duty_cycle_label', text="Duty cycle: ")
        self.duty_cycle_value = ui.create_line_edit(text='@binding(duty_cycle)',
                                                         name='duty_cycle_value', width='100')

        self.acquisition_adc_row = ui.create_row(self.acqusition_adc_text, self.acquisition_adc_value,
                                                 ui.create_stretch(),
                                                 self.duty_cycle_label, self.duty_cycle_value)

        self.cutoff_text = ui.create_label(name='cutoff_text', text='Cutoff (KHz): ')
        self.cutoff_value = ui.create_line_edit(name='cutoff_value', text='@binding(acquisition_cutoff)')

        self.window_text = ui.create_label(name='cutoff_text', text='Window: ')
        self.window_value = ui.create_combo_box(name='window_value',
                                                items=ACQUISITION_WINDOW,
                                                current_index='@binding(acquisition_window)')
        self.adc_filter_row = ui.create_row(self.cutoff_text, self.cutoff_value, ui.create_stretch(),
                                            self.window_text, self.window_value)

        self.adc_parameters_group = ui.create_group(title='ADC parameters', content=ui.create_column(
            self.filter_row, self.video_delay_row, self.acquisition_adc_row, self.kernel_mode_row, self.adc_filter_row
        ))

        #Hardware settings
        self.magswitches_text = ui.create_label(name='magswitches_text', text="Mag. Switches: ")
        self.magswitches_value = ui.create_line_edit(name='magswitches_value: ', text='@binding(magboard_switches)')
        self.magswitches_row = ui.create_row(self.magswitches_text, self.magswitches_value,
                                                  ui.create_stretch())

        self.offset_adc_text = ui.create_label(name='offset_adc_text', text="Off. ADC: ")
        self.offset_adc_value = ui.create_line_edit(name='offset_adc_value: ', text='@binding(offset_adc)')
        self.offset_adc_row = ui.create_row(self.offset_adc_text, self.offset_adc_value,
                                             ui.create_stretch())

        self.hardware_settings_group = ui.create_group(title='Hardware settings', content=ui.create_column(
            self.magswitches_row, self.offset_adc_row
        ))

        #Creating final GUI
        self.column = ui.create_column(self.acquisition_parameters_group, self.rastering_group, self.adc_parameters_group, self.hardware_settings_group)
        self.dialog = ui.create_modeless_dialog(self.column, title="Scan Settings")

class ConfigDialog:
    def __init__(self, document_controller):
        # document_controller_ui AND document_controller should be passed to the construct....
        self.widget = Declarative.construct(document_controller.ui, document_controller, View().dialog, Handler())
        if self.widget != None:
            self.widget.show()