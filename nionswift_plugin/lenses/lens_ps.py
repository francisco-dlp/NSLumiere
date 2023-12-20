import logging, numpy, threading, serial

from nion.instrumentation import HardwareSource
from . import Lens_controller

try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')
MAX_OBJ = 9.5
MAX_C1 = 1.5
MAX_C2 = 1.5

ANGLE_REFERENCE = set_file.settings["lenses"]["DISPLACEMENT_ANGLE_REFERENCE"]

DISPLACEMENT0 = float(set_file.settings["lenses"]["DISPLACEMENT_ARRAY"][0])
DISPLACEMENT1 = float(set_file.settings["lenses"]["DISPLACEMENT_ARRAY"][1])
DISPLACEMENT = [0.25 / DISPLACEMENT0, 0, 0.25 / DISPLACEMENT1, 0]

__author__ = "Yves Auad"

class Lenses(Lens_controller.LensesController):

    def __init__(self, sport):
        super().__init__()
        self.success = False
        self.ser = serial.Serial()
        self.ser.baudrate = 57600
        self.ser.port = sport
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        self.lock = threading.Lock()

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.success = True
        except:
            #1;11;255;1
            logging.info("***LENSES***: Could not find Lenses PS. Entering in debug mode.")

    def unblock_power_supply(self):
        string = '>1,11,255,1\r'
        self.ser.write(string.encode())
        return self.ser.readline()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        if self.success:
            try:
                self.ser.write(string.encode())
                self.ser.read(7)
                current = self.ser.read_until(expected=b','); current = current[:-1]
                voltage = self.ser.read_until(expected=b','); voltage = voltage[:-1]
                self.ser.readline()
            except:
                logging.info('***LENSES***: Communication Error over Serial Port. Easy check using Serial Port '
                             'Monitor software.')
        else:
            current = str(abs(numpy.random.randn(1)[0]) * 0.01 + 7.5).encode()
            voltage = str(abs(numpy.random.randn(1)[0]) * 0.1 + 42.5).encode()
        return current, voltage

    def set_val(self, val, which):
        if which == 'OBJ_STIG':
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_scan_device")
            if scan is not None:
                scan.scan_device.orsayscan.ObjectiveStigmateur(val[0] / 1000., val[1] / 1000.)
            else:
                logging.info('***LENSES***: Could not find objetive stigmator.')
            return
        elif which == 'OBJ_ALIG':
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            open_scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "open_scan_device")

            #Displacing the probe but following the angle reference
            if scan is not None:
                angle = scan.scan_device.scan_rotation
                angle = angle - ANGLE_REFERENCE
                new_dx = val[0] * DISPLACEMENT[0] * numpy.cos(numpy.radians(angle)) - val[2] * DISPLACEMENT[2] * numpy.sin(numpy.radians(angle))
                new_dy = val[0] * DISPLACEMENT[0] * numpy.sin(numpy.radians(angle)) + val[2] * DISPLACEMENT[2] * numpy.cos(numpy.radians(angle))
                scan.scan_device.orsayscan.AlObjective(new_dx, val[1] * DISPLACEMENT[1],
                                                       -new_dy,
                                                       val[3] * DISPLACEMENT[3])
            else:
                logging.info('***LENSES***: Could not displace dipole.')

            #Open scan displacement in debug mode for development
            if open_scan is not None and open_scan.scan_device.scan_engine.debug_io is not None:
                open_scan.scan_device.scan_engine.debug_io.probe_offset = [-val[0] * 4.05, -val[2] * 4.05]
            else:
                logging.info('***LENSES***: Could not debug OpenScan probe offset.')

            return
        elif which == 'GUN_STIG':
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            if scan is not None:
                scan.scan_device.orsayscan.CondensorStigmateur(val[0] / 1000., val[1] / 1000.)
            else:
                logging.info('***LENSES***: Could not find gun stigmator.')
            return
        elif which == 'OBJ' and val<=MAX_OBJ and val>=0:
            string_init = '>1,1,1,'
        elif which == 'C1' and val<=MAX_C1 and val>=0:
            string_init = '>1,1,2,'
        elif which == 'C2' and val<=MAX_C2 and val>=0:
            string_init = '>1,1,3,'
        else:
            logging.info("***LENSES***: Attempt to set values out of range.")
            return None

        if self.success:
            string = string_init + str(val) + ',0.5\r'
            self.ser.write(string.encode())
            return self.ser.readline()
        else:
            return None