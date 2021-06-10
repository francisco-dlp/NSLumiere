import serial
import logging

__author__ = "Yves Auad"

class AirLockVacuum:

    def __init__(self, sport):
        self.success = False
        self.ser=serial.Serial()
        self.ser.baudrate=9600
        self.ser.port=sport
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout=0.2

        try:
            if not self.ser.is_open:
                self.ser.open()
            self.success = True
        except:
            logging.info("***AIRLOCK GAUGE***: Could not find hardware. Entering in debug mode.")

    def query(self):
        try:
            self.ser.write(b'0010074002=?106\r')
            self.ser.read(10)
            data=self.ser.read(4).decode()
            ex=self.ser.read(2).decode()
            self.ser.read(4)
            value = int(data)/1000. * 10**(int(ex)-20)
            return value
        except:
            logging.info("***AIRLOCK GAUGE***: Problem querying gun gauge. Entering in debug mode.")
            return 0.0