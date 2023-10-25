import numpy
import time

from nion.typeshed import Interactive_1_0 as Interactive
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.swift.model import HardwareSource
from nion.data import Calibration


AUTOSTEM_CONTROLLER_ID = "autostem_controller"
autostem = HardwareSource.HardwareSourceManager().get_instrument_by_id(AUTOSTEM_CONTROLLER_ID)

sx_m = autostem.get_control_output(shift_x_control_name)
sy_m = autostem.get_control_output(shift_y_control_name)