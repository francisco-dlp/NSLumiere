import serial
import sys
import time
import os
import json

__author__ = "Yves Auad"

def _isPython3():
    return sys.version_info[0] >= 3


def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class OptSpectrometer:

    def __init__(self, sendmessage):
        self.sendmessage = sendmessage
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM16'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 60

        try:
            if not self.ser.is_open:
                self.ser.open()
                time.sleep(0.1)

                self.ser.write(b'?NM\r')
                wav_line = self.ser.readline()
                self.wavelength = float(wav_line[1:6].decode())

                self.ser.write(b'?GRATING\r')
                grating_line = self.ser.readline()
                self.now_grating = int(grating_line[1:2].decode())-1

                self.ser.write(b'EXIT-MIRROR ?MIRROR\r')
                mirror_line = self.ser.readline()
                if mirror_line[1:6].decode() == 'front':
                    self.which_slit=0
                else:
                    self.which_slit=1

                self.ser.write(b'SIDE-ENT-SLIT ?MICRONS\r')
                entrance_line = self.ser.readline()
                self.entrance_slit = float(entrance_line[1:5].decode())

                self.ser.write(b'SIDE-EXIT-SLIT ?MICRONS\r')
                exit_line = self.ser.readline()
                self.exit_slit = float(exit_line[1:5].decode())

                gratings=list()
                self.ser.write(b'?GRATINGS\r')
                msg = True
                while msg:
                    line = self.ser.readline()
                    if line:
                        if b'g/mm' in line:
                            gratings.append(line[4:-3].decode())
                    if line[-4:-2] == b'ok':
                        msg = False

                abs_path = os.path.abspath(os.path.join((__file__ + "/../../"), 'global_settings.json'))
                with open(abs_path) as savfile:
                    json_object = json.load(savfile)

                json_object["MONOCHROMATOR"]["GRATINGS"] = gratings

                with open(abs_path, 'w') as json_file:
                    json.dump(json_object, json_file, indent=4)
        except:
            self.sendmessage(1)

    def set_grating(self, value):
        string = str(value+1)+ ' GRATING\r'
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False
        self.sendmessage(2)

    def set_wavelength(self, value):
        if value>=0 and value<=1000:
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

    def set_entrance(self, value):
        if value>=0 and value<=5000:
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

    def set_exit(self, value):
        if value>=0 and value<=5000:
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

    def set_which(self, value):
        if value==0:
            string = 'EXIT-MIRROR FRONT 400 MS\r'
        if value==1:
            string = 'EXIT-MIRROR SIDE 400 MS\r'
        self.ser.write(string.encode())
        msg = True
        while msg:
            line = self.ser.readline()
            if b'ok' in line:
                msg = False

        self.sendmessage(6)