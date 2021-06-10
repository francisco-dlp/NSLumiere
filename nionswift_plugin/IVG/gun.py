import serial
import logging

__author__ = "Yves Auad"

class GunVacuum:

    def __init__(self, sport):
        self.success = False
        self.ser=serial.Serial()
        self.ser.baudrate=115200
        self.ser.port=sport
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.ser.write(b'GDAT? 1\n')
            self.ser.readline()
            self.success = True
        except:
            logging.info("***GUN GAUGE***: Could not find hardware. Entering in debug mode.")

    def query(self):
        try:
            self.ser.write(b'GDAT? 1\n')
            value=self.ser.read(15)
            value=value.decode()
            ex=int(value[-5:-1])
            sig=float(value[0:6])
            vide=sig * 10**ex
            return vide
        except:
            logging.info("***GUN GAUGE@IVG***: Problem querying gun gauge. Returning zero instead.")
            return 0