import logging, serial

try:
    from ..aux_files import read_data
except ImportError:
    from ..aux_files.config import read_data

set_file = read_data.FileManager('global_settings')

__author__ = "Yves Auad"

class ControllerAlim():

    def __init__(self, sport):
        self.success = False
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = sport
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.success = True
        except:
            logging.info("***CONTROL ALIM.***: Could not find controller. Entering in debug mode.")

    def set_val(self, group, dac, value):
        values = [str(group), str(dac), str(valeu)]
        message = (','.join(values) + '\n').encode()
        self.ser.write(message)
        return self.ser.readline()