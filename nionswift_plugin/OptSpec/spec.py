import serial
import logging
from ..aux_files import read_data

__author__ = "Yves Auad"

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class OptSpectrometer:

    def __init__(self, sendmessage, sport):
        self.sendmessage = sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = sport
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 60
        self.success = False

        try:
            if not self.ser.is_open:
                self.ser.open()

                self.ser.write(b'?NM\r')
                wav_line = self.ser.readline()
                self.wavelength = float(wav_line.split(b'nm')[0].decode())

                self.ser.write(b'?GRATING\r')
                grating_line = self.ser.readline()
                self.now_grating = int(grating_line.split(b'ok')[0].decode()) - 1

                self.ser.write(b'EXIT-MIRROR ?MIRROR\r')
                mirror_line = self.ser.readline()
                if mirror_line[1:6].decode() == 'front':
                    self.which_slit = 0
                else:
                    self.which_slit = 1

                self.ser.write(b'SIDE-ENT-SLIT ?MICRONS\r')
                entrance_line = self.ser.readline()
                self.entrance_slit = float(entrance_line.split(b'um')[0].decode())

                self.ser.write(b'SIDE-EXIT-SLIT ?MICRONS\r')
                exit_line = self.ser.readline()
                self.exit_slit = float(exit_line.split(b'um')[0].decode())
                self.success = True

        except Exception as e:
            set_file = read_data.FileManager('global_settings')
            com_port = set_file.settings["spectrometer"]["COM_PRINCETON"]
            path = set_file.abs_path
            logging.info(f"Princeton spectrometer: Could not initialize spectro. Current COM port is {com_port}. " \
                        f"Go to file {path} to change. Exception: {e}.")

    def try_open(self):
        if not self.ser.is_open:
            self.ser.open()
        if not self.ser.is_open:
            logging.info(f"Princeton spectrometer: Problem in USB port.")
            return

    def get_wavelength(self):
        self.try_open()
        self.ser.write(b'?NM\r')
        wav_line = self.ser.readline()
        return float(wav_line.split(b'nm')[0].decode())

    def set_wavelength(self, value):
        self.try_open()
        if value >= 0 and value <= 1000:
            string = (format(value, '.3f') + ' <goto>\r')

        else:
            string = (format(0, '.3f') + ' <goto>\r')
            self.sendmessage(7)
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(3)

    def get_grating(self):
        self.try_open()
        self.ser.write(b'?GRATING\r')
        grating_line = self.ser.readline()
        return int(grating_line.split(b'ok')[0].decode()) - 1

    def set_grating(self, value):
        self.try_open()
        string = str(value + 1) + ' GRATING\r'
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(2)

    def get_entrance(self):
        self.try_open()
        self.ser.write(b'SIDE-ENT-SLIT ?MICRONS\r')
        entrance_line = self.ser.readline()
        return float(entrance_line.split(b'um')[0].decode())

    def set_entrance(self, value):
        self.try_open()
        if value >= 0 and value <= 5000:
            string = 'SIDE-ENT-SLIT ' + format(value, '.0f') + ' MICRONS\r'
        else:
            string = 'SIDE-ENT-SLIT ' + str(3000) + ' MICRONS\r'
            self.sendmessage(7)
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(4)

    def get_exit(self):
        self.try_open()
        self.ser.write(b'SIDE-EXIT-SLIT ?MICRONS\r')
        exit_line = self.ser.readline()
        return float(exit_line.split(b'um')[0].decode())

    def set_exit(self, value):
        self.try_open()
        if value >= 0 and value <= 5000:
            string = 'SIDE-EXIT-SLIT ' + format(value, '.0f') + ' MICRONS\r'
        else:
            string = 'SIDE-EXIT-SLIT ' + str(3000) + ' MICRONS\r'
            self.sendmessage(7)
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(5)

    def get_which(self):
        self.try_open()
        self.ser.write(b'EXIT-MIRROR ?MIRROR\r')
        mirror_line = self.ser.readline()
        if mirror_line[1:6].decode() == 'front':
            return 0
        else:
            return 1

    def set_which(self, value):
        self.try_open()
        if value == 0:
            string = 'EXIT-MIRROR FRONT 400 MS\r'
        if value == 1:
            string = 'EXIT-MIRROR SIDE 400 MS\r'
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(6)

    def gratingNames(self):
        self.try_open()
        gratings = list()
        self.ser.write(b'?GRATINGS\r')
        msg = True
        while msg:
            line = self.ser.readline()
            if line:
                if b'g/mm' in line:
                    gratings.append(line[4:-3].decode())
            if line[-4:-2] == b'ok':
                msg = False
        return gratings

    def gratingLPMM(self):
        self.try_open()
        self.lp_mm = list()
        self.ser.write(b'?GRATINGS\r')
        msg = True
        while msg:
            line = self.ser.readline()
            if line:
                if b'g/mm' in line:
                    self.lp_mm.append(float(line[4:8].decode()))
            if line[-4:-2] == b'ok':
                msg = False
        return self.lp_mm

    def get_specFL(self):
        return 300.0

    def which_camera(self):
        return 'orsay_camera_eire'

    def camera_pixels(self):
        return 1600

    def deviation_angle(self):
        return 0.53