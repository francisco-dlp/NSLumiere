import sys
import logging
import time
import threading
import numpy
import abc

__author__ = "Yves Auad"

class LensesController(abc.ABC):

    def __init__(self):
        self.lock = threading.Lock()

    @abc.abstractmethod
    def query(self, which):
        """Query Lens"""

    @abc.abstractmethod
    def set_val(self, val, which):
        """Set Lens Value"""

    def locked_query(self, which):
        with self.lock:
            return self.query(which)

    def locked_set_val(self, val, which):
        with self.lock:
            return self.set_val(val, which)

    def wobbler_loop(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.set_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / frequency)
            self.set_val(current, which)

    def wobbler_on(self, current, intensity, frequency, which):
        self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, frequency, which), )
        self.wobbler_thread.start()

    def wobbler_off(self):
        self.wobbler_thread.do_run = False
