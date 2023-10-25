import numpy
import time

from nion.typeshed import Interactive_1_0 as Interactive
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.swift.model import HardwareSource
from nion.data import Calibration


AUTOSTEM_CONTROLLER_ID = "autostem_controller"
STEP = 3.0e-9
LOOPS = 60

autostem = HardwareSource.HardwareSourceManager().get_instrument_by_id(AUTOSTEM_CONTROLLER_ID)
shift_x_control_name = "SShft.x"
shift_y_control_name = "SShft.y"

for x in range(LOOPS):
    sx_m = autostem.get_control_output(shift_x_control_name)
    sy_m = autostem.get_control_output(shift_y_control_name)
    autostem.set_control_output(shift_x_control_name, sx_m + STEP)
    time.sleep(1)