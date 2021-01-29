import time
import threading
import abc

__author__ = "Yves Auad"

class LensesController(abc.ABC):

    def __init__(self):
        self.lock = threading.Lock()
        self.wobbler_thread = threading.Thread()

    @abc.abstractmethod
    def query(self, which):
        """
        Query Lens
        """

    @abc.abstractmethod
    def set_val(self, val, which):
        """
        Set Lens Value
        """

    @abc.abstractmethod
    def query_stig(self, which):
        """
        Query Stigmator
        """

    @abc.abstractmethod
    def set_val_stig(self, val, which):
        """"
        Set Val Stigmator.
        The value must be between -1000 and +1000 in order to accord the slides.
        """



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
        if self.wobbler_thread.is_alive():
            self.wobbler_off()
        if not self.wobbler_thread.is_alive():
            self.wobbler_thread = threading.Thread(target=self.wobbler_loop, args=(current, intensity, frequency, which), )
            self.wobbler_thread.start()

    def wobbler_off(self):
        if self.wobbler_thread.is_alive():
            self.wobbler_thread.do_run = False
            self.wobbler_thread.join()