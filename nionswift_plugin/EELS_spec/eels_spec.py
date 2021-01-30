import serial

__author__ = "Yves Auad"

class EELS_Spectrometer(EELS_controller.EELSController):

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM4'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
        except:
            logging.info("***EELS SPECTROMETER***: Could not find EELS Spec. Check Hardware")

    def set_spec_val(self, val, which):
        if which=='dmx':
            which = 'al'
        if abs(val)<32767:
            try:
                if val < 0:
                    val = abs(val)
                else:
                    val = 0xffff - val
                string = which + ' 0,' + hex(val)[2:6] + '\r'
                self.ser.write(string.encode())
                return self.ser.read(6)
            except:
                logging.info(
                    "***EELS SPECTROMETER***: Problem communicating over serial port. Easy check using Serial Port Monitor.")
        else:
            logging.info("***EELS SPECTROMETER***: Attempt to write a value out of range.")