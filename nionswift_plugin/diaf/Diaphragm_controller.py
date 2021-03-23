import abc

__author__ = "Yves Auad"

class Aperture_Controller(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def set_val(self, which, value):
        """
        Set the value of the correspondent aperture.
        """

    @abc.abstractmethod
    def get_val(self, which):
        """
        Get the value of the correspondent aperture.
        """