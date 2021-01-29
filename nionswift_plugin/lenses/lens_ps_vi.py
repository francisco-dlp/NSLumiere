import sys
import logging
import time
import threading
import numpy

from . import lens_controller

__author__ = "Yves Auad"

class Lenses(lens_controller.LensesController):

    def __init__(self):
        super().__init__()

    def query(self, which):
        if which == 'obj':
            string = '>1,2,1\r'
        if which == 'c1':
            string = '>1,2,2\r'
        if which == 'c2':
            string = '>1,2,3\r'
        current = str(abs(numpy.random.randn(1)[0]) * 0.01 + 7.5).encode()
        voltage = str(abs(numpy.random.randn(1)[0]) * 0.1 + 42.5).encode()
        return current, voltage

    def set_val(self, val, which):
        if which == 'obj':
            string_init = '>1,1,1,'
        if which == 'c1':
            string_init = '>1,1,2,'
        if which == 'c2':
            string_init = '>1,1,3,'
        string = string_init + str(val) + ',0.5\r'
        logging.info(string)
        if val < 0:
            logging.info("***LENSES***: Attempt to set values out of range.")

    def set_val_stig(self, val, which):
        pass

    def query_stig(self, which):
        return 0



