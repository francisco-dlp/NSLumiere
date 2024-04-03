from nion.ui import Declarative
from nion.utils import Event
from nion.swift.model import HardwareSource

ACQUISITION_WINDOW = ['boxcar', 'triang', 'blackman', 'hamming', 'hann']
KERNEL_LIST = ['None', 'Square', 'Triangular', 'Gaussian', 'Blackman', 'Custom', 'First pixel', 'Last pixel', 'Given pixel']
SCAN_MODES = ['Normal', 'Serpentine', 'Random', 'Mini-scans', 'MikePath', 'Lissajous', 'Sawtooth Lissajous']
IMAGE_VIEW_MODES = ['Normal', 'Ordered', 'DAC-based', 'Low-pass filter', 'Inpainting']
ADC_READOUT_MODES = ['FIR', 'Pixel counter', 'IIR', 'Multip.', 'Kernel', 'Fixed TAP']
OUTPUT_TYPES_MUX = ['Pixel logic', 'Paused logic', 'New frame logic', 'Pulse out', 'I1TTL', 'I2TTL', 'I3TTL',
                    'Clock divider', 'Input divider']
OUTPUT_INPUT_TO_DIVIDE = ['I1TTL', 'I2TTL', 'I3TTL']

class Handler:
    def __init__(self):
        scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("open_scan_device")
        self.scan = scan.scan_device.scan_engine


class View():
    def __init__(self):
        ui = Declarative.DeclarativeUI()

        # FIRST TAB (GENERAL_PARAMETERS)
        self.imageshow_text = ui.create_label(name='imageshow_text', text="Image display: ")
        self.imageshow_value = ui.create_combo_box(
            items=IMAGE_VIEW_MODES,
            current_index='@binding(scan.imagedisplay)',
            name='rastering_value', width='100')
        self.image_filter_intensity_text = ui.create_label(name='image_filter_intensity_text', text='Filter intensity: ')
        self.image_filter_intensity_value = ui.create_line_edit(name='image_filter_intensity_value', text='@binding(scan.imagedisplay_filter_intensity)')
        self.imageshow_row = ui.create_row(self.imageshow_text, self.imageshow_value, ui.create_spacing(10),
                                           self.image_filter_intensity_text, self.image_filter_intensity_value,
                                           ui.create_stretch())

        self.acquisition_parameters_group = ui.create_group(title='Acquisition parameters', content=ui.create_column(
            self.imageshow_row
        ))

        #Rastering parameters
        self.flyback_text = ui.create_label(name='flyback_text', text="Flyback value (us): ")
        self.flyback_value = ui.create_line_edit(name='flyback_value', text='@binding(scan.flyback_us)')
        self.flyback_row = ui.create_row(self.flyback_text, self.flyback_value, ui.create_stretch())

        self.external_trigger_text = ui.create_label(name='external_trigger_text', text="External Trigger: ")
        self.external_trigger = ui.create_check_box(name='external_trigger', checked='@binding(scan.external_trigger)')
        self.external_trigger_row = ui.create_row(self.external_trigger_text, self.external_trigger,
                                                  ui.create_stretch())

        self.rastering_text = ui.create_label(name='rastering_text', text="Rastering mode: ")
        self.rastering_value = ui.create_combo_box(items=SCAN_MODES,
                                                   current_index='@binding(scan.rastering_mode)',
                                                   name='rastering_value', width='100')
        self.mini_scan_text = ui.create_label(name='mini_scan_text', text="Mini-scans: ")
        self.mini_scan_value = ui.create_line_edit(name='mini_scan_value', text='@binding(scan.mini_scan)', width='100')
        self.rastering_row = ui.create_row(self.rastering_text, self.rastering_value, ui.create_stretch(),
                                           self.mini_scan_text, self.mini_scan_value)

        self.lissajous_nx_text = ui.create_label(name='lissajous_text', text="Liss. X (Hz): ")
        self.lissajous_nx_value = ui.create_line_edit(name='lissajous_value: ', width=45, text='@binding(scan.lissajous_nx)')
        self.lissajous_ny_text = ui.create_label(name='lissajous_text', text="Liss. Y: (Hz) ")
        self.lissajous_ny_value = ui.create_line_edit(name='lissajous_value: ', width=45, text='@binding(scan.lissajous_ny)')
        self.lissajous_phase_text = ui.create_label(name='lissajous_phase_text', text="Lissajous phase: ")
        self.lissajous_phase_value = ui.create_line_edit(name='lissajous_phase_value: ', width=30,
                                                         text='@binding(scan.lissajous_phase)')
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
                                                current_index='@binding(scan.kernel_mode)',
                                                name='kernel_mode_value', width='100')
        self.kernel_given_pixel_label = ui.create_label(text='Given pixel: ')
        self.kernel_given_pixel_value = ui.create_line_edit(name='kernel_given_pixel_value',
                                                            text='@binding(scan.given_pixel)', width=45)
        self.kernel_mode_row = ui.create_row(self.kernel_mode_text, self.kernel_mode_value, ui.create_stretch(),
                                             self.kernel_given_pixel_label, self.kernel_given_pixel_value)

        self.filter_text = ui.create_label(name='filter_text', text="IIR Filter: ")
        self.filter_value = ui.create_combo_box(items=['1', '2', '4', '8', '16', '32', '64'],
                                                current_index='@binding(scan.dsp_filter)',
                                                name='filter_value', width = '100')
        self.filter_row = ui.create_row(self.filter_text, self.filter_value, ui.create_stretch())

        self.video_delay_text = ui.create_label(name='video_delay_text', text="Video delay: ")
        self.video_delay_value = ui.create_line_edit(text='@binding(scan.video_delay)',
                                                name='video_delay_value', width='100')
        self.enable_pause_sampling = ui.create_check_box(name='enable_pause_sampling', text="Pause Sampling", checked='@binding(scan.pause_sampling)')
        self.video_delay_row = ui.create_row(self.video_delay_text, self.video_delay_value, ui.create_stretch(), self.enable_pause_sampling)

        self.acqusition_adc_text = ui.create_label(name='acqusition_adc_text', text="ADC type: ")
        self.acquisition_adc_value = ui.create_combo_box(items=ADC_READOUT_MODES,
                                                current_index='@binding(scan.adc_acquisition_mode)',
                                                name='acquisition_adc_value', width='100')
        self.duty_cycle_label = ui.create_label(name='duty_cycle_label', text="Duty cycle: ")
        self.duty_cycle_value = ui.create_line_edit(text='@binding(scan.duty_cycle)',
                                                         name='duty_cycle_value', width='100')

        self.acquisition_adc_row = ui.create_row(self.acqusition_adc_text, self.acquisition_adc_value,
                                                 ui.create_stretch(),
                                                 self.duty_cycle_label, self.duty_cycle_value)

        self.cutoff_text = ui.create_label(name='cutoff_text', text='Cutoff (KHz): ')
        self.cutoff_value = ui.create_line_edit(name='cutoff_value', text='@binding(scan.acquisition_cutoff)')

        self.window_text = ui.create_label(name='cutoff_text', text='Window: ')
        self.window_value = ui.create_combo_box(name='window_value',
                                                items=ACQUISITION_WINDOW,
                                                current_index='@binding(scan.acquisition_window)')
        self.adc_filter_row = ui.create_row(self.cutoff_text, self.cutoff_value, ui.create_stretch(),
                                            self.window_text, self.window_value)

        self.adc_parameters_group = ui.create_group(title='ADC parameters', content=ui.create_column(
            self.filter_row, self.video_delay_row, self.acquisition_adc_row, self.kernel_mode_row, self.adc_filter_row
        ))

        #Hardware settings
        self.magswitches_text = ui.create_label(name='magswitches_text', text="Mag. Switches: ")
        self.magswitches_value = ui.create_line_edit(name='magswitches_value: ', text='@binding(scan.magboard_switches)')
        self.magswitches_row = ui.create_row(self.magswitches_text, self.magswitches_value,
                                                  ui.create_stretch())

        self.offset_adc_text = ui.create_label(name='offset_adc_text', text="Offset ADC (V): ")
        self.offset_adc0_value = ui.create_line_edit(text='@binding(scan.offset_adc0)', width=50)
        self.offset_adc1_value = ui.create_line_edit(text='@binding(scan.offset_adc1)', width=50)
        self.offset_adc2_value = ui.create_line_edit(text='@binding(scan.offset_adc2)', width=50)
        self.offset_adc3_value = ui.create_line_edit(text='@binding(scan.offset_adc3)', width=50)
        self.offset_adc4_value = ui.create_line_edit(text='@binding(scan.offset_adc4)', width=50)
        self.offset_adc5_value = ui.create_line_edit(text='@binding(scan.offset_adc5)', width=50)
        self.offset_adc_row = ui.create_row(self.offset_adc_text, self.offset_adc0_value, self.offset_adc1_value,
                                            self.offset_adc2_value, self.offset_adc3_value, self.offset_adc4_value,
                                            self.offset_adc5_value,
                                             ui.create_stretch())

        self.multiblock_text = ui.create_label(text="Ext. Multiblock: ")
        self.multiblock0_value = ui.create_line_edit(text='@binding(scan.multiblock0)', width=40)
        self.multiblock1_value = ui.create_line_edit(text='@binding(scan.multiblock1)', width=40)
        self.multiblock2_value = ui.create_line_edit(text='@binding(scan.multiblock2)', width=40)
        self.multiblock3_value = ui.create_line_edit(text='@binding(scan.multiblock3)', width=40)
        self.multiblock_row = ui.create_row(self.multiblock_text, self.multiblock0_value, self.multiblock1_value,
                                            self.multiblock2_value, self.multiblock3_value,
                                            ui.create_stretch())

        self.mag_multiblock_text = ui.create_label(text="MAG Multiblock: ")
        self.mag_multiblock0_value = ui.create_line_edit(text='@binding(scan.mag_multiblock0)', width=30)
        self.mag_multiblock1_value = ui.create_line_edit(text='@binding(scan.mag_multiblock1)', width=30)
        self.mag_multiblock2_value = ui.create_line_edit(text='@binding(scan.mag_multiblock2)', width=30)
        self.mag_multiblock3_value = ui.create_line_edit(text='@binding(scan.mag_multiblock3)', width=30)
        self.mag_multiblock4_value = ui.create_line_edit(text='@binding(scan.mag_multiblock4)', width=30)
        self.mag_multiblock5_value = ui.create_line_edit(text='@binding(scan.mag_multiblock5)', width=30)
        self.mag_multiblock_row = ui.create_row(self.mag_multiblock_text, self.mag_multiblock0_value, self.mag_multiblock1_value,
                                            self.mag_multiblock2_value, self.mag_multiblock3_value, self.mag_multiblock4_value,
                                                self.mag_multiblock5_value, ui.create_stretch())

        self.hardware_settings_group = ui.create_group(title='Hardware settings', content=ui.create_column(
            self.magswitches_row, self.offset_adc_row, self.multiblock_row, self.mag_multiblock_row
        ))

        self.first_tab = ui.create_tab(label="General Parameters", content=ui.create_column(
            self.acquisition_parameters_group, self.rastering_group, self.adc_parameters_group,
            self.hardware_settings_group))

        #SECOND TAB (Input multiplexing)
        self.input1_label = ui.create_label(text='Input 1: ')
        self.input11_value = ui.create_radio_button(text='ADC1', value=0, group_value='@binding(scan.input1_mux)')
        self.input12_value = ui.create_radio_button(text='ADC2', value=1, group_value='@binding(scan.input1_mux)')
        self.input13_value = ui.create_radio_button(text='ADC3', value=2, group_value='@binding(scan.input1_mux)')
        self.input14_value = ui.create_radio_button(text='ADC4', value=3, group_value='@binding(scan.input1_mux)')
        self.input15_value = ui.create_radio_button(text='ADC5', value=4, group_value='@binding(scan.input1_mux)')
        self.input16_value = ui.create_radio_button(text='ADC6', value=5, group_value='@binding(scan.input1_mux)')
        self.input17_value = ui.create_radio_button(text='Pulse1', value=6, group_value='@binding(scan.input1_mux)')
        self.input1_row=ui.create_row(self.input1_label, self.input11_value, self.input12_value, self.input13_value,
                                      self.input14_value, self.input15_value, self.input16_value,
                                      self.input17_value, ui.create_stretch())

        self.input2_label = ui.create_label(text='Input 2: ')
        self.input21_value = ui.create_radio_button(text='ADC1', value=0, group_value='@binding(scan.input2_mux)')
        self.input22_value = ui.create_radio_button(text='ADC2', value=1, group_value='@binding(scan.input2_mux)')
        self.input23_value = ui.create_radio_button(text='ADC3', value=2, group_value='@binding(scan.input2_mux)')
        self.input24_value = ui.create_radio_button(text='ADC4', value=3, group_value='@binding(scan.input2_mux)')
        self.input25_value = ui.create_radio_button(text='ADC5', value=4, group_value='@binding(scan.input2_mux)')
        self.input26_value = ui.create_radio_button(text='ADC6', value=5, group_value='@binding(scan.input2_mux)')
        self.input27_value = ui.create_radio_button(text='Pulse2', value=6, group_value='@binding(scan.input2_mux)')
        self.input2_row = ui.create_row(self.input2_label, self.input21_value, self.input22_value, self.input23_value,
                                        self.input24_value, self.input25_value, self.input26_value,
                                      self.input27_value, ui.create_stretch())

        self.inputx_label = ui.create_label(text='Route to X: ')
        self.inputx0_value = ui.create_radio_button(text='None', value=0, group_value='@binding(scan.routex_mux)')
        self.inputx1_value = ui.create_radio_button(text='ADC1', value=1, group_value='@binding(scan.routex_mux)')
        self.inputx2_value = ui.create_radio_button(text='ADC2', value=2, group_value='@binding(scan.routex_mux)')
        self.inputx3_value = ui.create_radio_button(text='ADC3', value=3, group_value='@binding(scan.routex_mux)')
        self.inputx4_value = ui.create_radio_button(text='ADC4', value=4, group_value='@binding(scan.routex_mux)')

        self.inputx_intensity_label = ui.create_label(text='Intensity: ')
        self.inputx_intensity = ui.create_line_edit(text='@binding(scan.routex_mux_intensity)', width=50)
        self.inputx_intensity_row = ui.create_row(self.inputx_intensity_label, self.inputx_intensity, ui.create_stretch())

        self.inputx_avg_label = ui.create_label(text='Averages: ')
        self.inputx_avg = ui.create_line_edit(text='@binding(scan.routex_mux_averages)', width=50)
        self.inputx_avg_row = ui.create_row(self.inputx_avg_label, self.inputx_avg,
                                                  ui.create_stretch())

        self.inputx_row = ui.create_row(self.inputx_label, self.inputx0_value, self.inputx1_value, self.inputx2_value,
                                        self.inputx3_value, self.inputx4_value, ui.create_stretch())
        self.inputx_group = ui.create_group(name='Route X', content=ui.create_column(self.inputx_row, self.inputx_intensity_row, self.inputx_avg_row))

        self.inputy_label = ui.create_label(text='Route to Y: ')
        self.inputy0_value = ui.create_radio_button(text='None', value=0, group_value='@binding(scan.routey_mux)')
        self.inputy1_value = ui.create_radio_button(text='ADC1', value=1, group_value='@binding(scan.routey_mux)')
        self.inputy2_value = ui.create_radio_button(text='ADC2', value=2, group_value='@binding(scan.routey_mux)')
        self.inputy3_value = ui.create_radio_button(text='ADC3', value=3, group_value='@binding(scan.routey_mux)')
        self.inputy4_value = ui.create_radio_button(text='ADC4', value=4, group_value='@binding(scan.routey_mux)')

        self.inputy_intensity_label = ui.create_label(text='Intensity: ')
        self.inputy_intensity = ui.create_line_edit(text='@binding(scan.routey_mux_intensity)', width=50)
        self.inputy_intensity_row = ui.create_row(self.inputy_intensity_label, self.inputy_intensity,
                                                  ui.create_stretch())

        self.inputy_avg_label = ui.create_label(text='Averages: ')
        self.inputy_avg = ui.create_line_edit(text='@binding(scan.routey_mux_averages)', width=50)
        self.inputy_avg_row = ui.create_row(self.inputy_avg_label, self.inputy_avg,
                                            ui.create_stretch())

        self.inputy_row = ui.create_row(self.inputy_label, self.inputy0_value, self.inputy1_value, self.inputy2_value,
                                        self.inputy3_value, self.inputy4_value, ui.create_stretch())
        self.inputy_group = ui.create_group(name='Route Y', content=ui.create_column(self.inputy_row, self.inputy_intensity_row, self.inputy_avg_row))

        self.second_tab = ui.create_tab(label='Input MUX', content=ui.create_column(
            self.input1_row, self.input2_row, self.inputx_group, self.inputy_group, ui.create_stretch()))

        #THIRD TAB (Output multiplexing)
        def create_output_mux(name: str, channel: str):
            output_label = ui.create_label(text=name)
            output_type = ui.create_combo_box(name='output'+channel+'_type', items=OUTPUT_TYPES_MUX,
                                               current_index='@binding(scan.output'+channel+'_mux_type)')
            output_freq_label = ui.create_label(text='Freq (Hz): ')
            output_freq = ui.create_line_edit(name='output1_freq', text='@binding(scan.output'+channel+'_mux_freq)')
            output_input = ui.create_combo_box(name='output'+channel+'_input', items=OUTPUT_INPUT_TO_DIVIDE,
                                                current_index='@binding(scan.output'+channel+'_mux_input)')
            output_input_div = ui.create_combo_box(name='output'+channel+'_input', items=['2', '4', '8', '16', '32'],
                                                     current_index='@binding(scan.output'+channel+'_mux_input_div)')
            output_delay = ui.create_line_edit(name='output1_delay', text='@binding(scan.output' + channel + '_mux_delay)')

            output_row=ui.create_row(output_label, output_type, output_freq_label, output_freq,
                                           output_input, output_input_div, output_delay, ui.create_stretch())
            return output_row


        self.third_tab = ui.create_tab(label='Output MUX', content=ui.create_column(
            create_output_mux('Output 1: ', '1'), create_output_mux('Output 2: ', '2'), create_output_mux('Output 3: ', '3'),
            create_output_mux('Output 4: ', '4'), create_output_mux('External: ', '5'), ui.create_stretch()))


        #Creating final GUI
        self.column = ui.create_tabs(self.first_tab, self.second_tab, self.third_tab)
        self.dialog = ui.create_modeless_dialog(self.column, title="Scan Settings")

class ConfigDialog:
    def __init__(self, document_controller):
        # document_controller_ui AND document_controller should be passed to the construct....
        self.widget = Declarative.construct(document_controller.ui, document_controller, View().dialog, Handler())
        if self.widget != None:
            self.widget.show()