import logging, serial, time

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
        self.ser.baudrate = 19200
        self.ser.port = sport
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.5
        self.__attempts = 0
        self.__max_attemps = 10

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.success = True
        except:
            logging.info("***CONTROL ALIM.***: Could not find controller. Entering in debug mode.")

    def set_val(self, group, dac, value):
        values = [str(group), str(dac), str(value)]
        message = (','.join(values) + '\n').encode()
        self.ser.write(message)
        is_ok = self.ser.readline() == b"OK\r\n"
        if not is_ok and self.__attempts < self.__max_attemps:
            self.__attempts += 1
            return self.set_val(group, dac, value)
        self.__attempts = 0
        return is_ok