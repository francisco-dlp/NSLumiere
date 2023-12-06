import logging
import threading
import numpy

from nion.instrumentation import HardwareSource
DISPLACEMENT = [0.25 / 2343.2, 0, 0.25 / 2421.8, 0]
ANGLE_REFERENCE = 316

from . import Lens_controller

__author__ = "Yves Auad"

class Lenses(Lens_controller.LensesController):

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        current = str(abs(numpy.random.randn(1)[0]) * 0.01 + 7.5).encode()
        voltage = str(abs(numpy.random.randn(1)[0]) * 0.1 + 42.5).encode()
        return current, voltage

    def set_val(self, val, which):
        if which == 'OBJ_STIG':
            logging.info(f'Obj. Stig value is {val}.')
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
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

            if scan is not None:
                angle = scan.scan_device.scan_rotation
                angle = angle - ANGLE_REFERENCE
                new_dx = val[0] * DISPLACEMENT[0] * numpy.cos(numpy.radians(angle)) - val[2] * DISPLACEMENT[2] * numpy.sin(numpy.radians(angle))
                new_dy = val[0] * DISPLACEMENT[0] * numpy.sin(numpy.radians(angle)) + val[2] * DISPLACEMENT[2] * numpy.cos(numpy.radians(angle))
                scan.scan_device.orsayscan.AlObjective(new_dx, val[1] * DISPLACEMENT[1],
                                                       -new_dy,
                                                       val[3] * DISPLACEMENT[3])
            else:
                logging.info('***LENSES***: Could not align objetive lens.')

            if open_scan is not None and open_scan.scan_device.scan_engine.debug_io is not None:
                open_scan.scan_device.scan_engine.debug_io.probe_offset = [-val[0] * 4.05, -val[2] * 4.05]
            else:
                logging.info('***LENSES***: Could not debug OpenScan probe offset.')

            return
        elif which == 'GUN_STIG':
            logging.info(f'Gun. Stig value is {val}.')
            scan = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            if scan is not None:
                scan.scan_device.orsayscan.CondensorStigmateur(val[0] / 1000., val[1] / 1000.)
            else:
                logging.info('***LENSES***: Could not find gun stigmator.')
            return
        elif which == 'OBJ':
            string_init = '>1,1,1,'
        elif which == 'C1':
            string_init = '>1,1,2,'
        elif which == 'C2':
            string_init = '>1,1,3,'
        string = string_init + str(val) + ',0.5\r'
        logging.info(string)