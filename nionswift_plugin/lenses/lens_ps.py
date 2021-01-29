import serial
import sys
import time
import threading
import os
import json
import logging

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

MAX_OBJ = settings["lenses"]["MAX_OBJ"]
MAX_C1 = settings["lenses"]["MAX_C1"]
MAX_C2 = settings["lenses"]["MAX_C2"]

__author__ = "Yves Auad"

class Lenses:

    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baudrate = 57600
        self.ser.port = 'COM13'
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.timeout = 0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
        except:
            logging.info("***LENSES***: Could not find Lenses PS")

        self.ser.readline()

    def query(self, which):
        if which == 'OBJ':
            string = '>1,2,1\r'
        if which == 'C1':
            string = '>1,2,2\r'
        if which == 'C2':
            string = '>1,2,3\r'
        try:
            self.ser.write(string.encode())
            self.ser.read(7)
            current = self.ser.read_until(expected=b','); current = current[:-1]
            voltage = self.ser.read_until(expected=b','); voltage = voltage[:-1]
            self.ser.readline()
        except:
            logging.info('***LENSES***: Communication Error over Serial Port. Easy check using Serial Port '
                         'Monitor software.')
        return current, voltage

    def set_val(self, val, which):
        if which == 'OBJ' and val<=MAX_OBJ and val>=0:
            string_init = '>1,1,1,'
        elif which == 'C1' and val<=MAX_C1 and val>=0:
            string_init = '>1,1,2,'
        elif which == 'C2' and val<=MAX_C2 and val>=0:
            string_init = '>1,1,3,'
        else:
            logging.info("***LENSES***: Attempt to set values out of range.")
            return None
        string = string_init + str(val) + ',0.5\r'
        self.ser.write(string.encode())
            return self.ser.readline()

    def query_stig(self, which):
        """
        0 -> Objective Stig 00
        1 -> Objective Stig 01
        2 -> Gun Stig 00
        3 -> Gun Stig 01
        """
        hardware = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")
        if which=='obj_stig_00':
            val = hardware.obj_stig00_f
        elif which == 'obj_stig_01':
            val = hardware.obj_stig01_f
        elif which == 'gun_stig_02':
            val = hardware.gun_stig00_f
        elif which == 'gun_stig_03':
            val = hardware.gun_stig01_f
        return val

    ef set_val_stig(self, val, which):
        """
        0 -> Objective Stig 00
        1 -> Objective Stig 01
        2 -> Gun Stig 00
        3 -> Gun Stig 01
        """
        hardware = HardwareSource.HardwareSourceManager().get_instrument_by_id("VG_Lum_controller")
        if which=='obj_stig_00':
            hardware.obj_stig00_f = val
        elif which=='obj_stig_01':
            hardware.obj_stig01_f = val
        elif which=='gun_stig_02':
            hardware.gun_stig00_f = val
        elif which=='gun_stig_03':
            hardware.gun_stig01_f = val




