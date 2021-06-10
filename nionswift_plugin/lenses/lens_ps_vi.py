import logging
import time
import threading
import numpy

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
            return
        if which == 'GUN_STIG':
            logging.info(f'Gun. Stig value is {val}.')
            return
        if which == 'OBJ':
            string_init = '>1,1,1,'
        if which == 'C1':
            string_init = '>1,1,2,'
        if which == 'C2':
            string_init = '>1,1,3,'
        string = string_init + str(val) + ',0.5\r'
        logging.info(string)
        if val < 0:
            self.sendmessage(2)