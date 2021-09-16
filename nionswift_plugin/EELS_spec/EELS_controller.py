import time
import threading
import abc

__author__ = "Yves Auad"

class EELSController(abc.ABC):

    def __init__(self):
        self.lock = threading.Lock()
        self.wobbler_thread = threading.Thread()
        self.last_wobbler_value = 0
        self.last_wobbler_which = 'OFF'

    @abc.abstractmethod
    def set_val(self, val, which):
        """
        Set value of the spectrometer.
        """

    def locked_set_val(self, val, which):
        with self.lock:
            self.set_val(val, which)

    def wobbler_loop(self, current, intensity, which):
        self.wobbler_thread = threading.currentThread()
        sens = 1
        while getattr(self.wobbler_thread, "do_run", True):
            sens = sens * -1
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.locked_set_val(current + sens * intensity, which)
            if getattr(self.wobbler_thread, "do_run", True): time.sleep(1. / 2.)
            self.locked_set_val(current, which)

    def wobbler_on(self, current, intensity, which):
        self.last_wobbler_which = which
        self.last_wobbler_value = current
        if self.wobbler_thread.is_alive():
            self.wobbler_off()
        if not self.wobbler_thread.is_alive():
            self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, which), )
            self.wobbler_thread.start()

    def wobbler_off(self):
        if self.wobbler_thread.is_alive():
            self.wobbler_thread.do_run = False
            self.wobbler_thread.join()
            self.locked_set_val(self.last_wobbler_value, self.last_wobbler_which)
