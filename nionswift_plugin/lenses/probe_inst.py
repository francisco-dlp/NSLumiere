# standard libraries
import json
import os
import logging

from nion.utils import Event
from nion.utils import Observable

abs_path = os.path.abspath(os.path.join((__file__+"/../../"), 'global_settings.json'))
with open(abs_path) as savfile:
    settings = json.load(savfile)

DEBUG = settings["lenses"]["DEBUG"]

if DEBUG:
    from . import lens_ps_vi as lens_ps
else:
    from . import lens_ps as lens_ps

class probeDevice(Observable.Observable):
    def __init__(self, nLens, LensNames, nStig, StigNames):
        self.property_changed_event = Event.Event()
        self.busy_event = Event.Event()

        self.__lenses_ps = lens_ps.Lenses()

        """
        MagLens:
        0 -> Objective Lens
        1 -> Condenser Lens 01
        2 -> Condenser Lens 02
        """

        self.__nLens = nLens
        self.__magLens = [0] * nLens
        self.__magLensGlobal = [True] * nLens
        self.__magLensWobbler = [False] * nLens
        self.__magLensNames = LensNames
        assert len(self.__magLensNames) == nLens

        """
        Stig:
        0 -> Objective 0
        1 -> Objective 1
        2 -> Gun 0
        3 - > Gun 1
        """

        self.__nStig = nStig
        self.__Stig = [0] * nStig
        self.__StigNames = StigNames
        assert len(self.__StigNames) == nStig


        """
        Wobbler intensity and frequency
        """
        self.wobbler_frequency_f = 2
        self.__wobbler_intensity = 0.02

    def init_handler(self):
        try:
            inst_dir = os.path.dirname(__file__)
            abs_path = os.path.join(inst_dir, 'lenses_settings.json')
            with open(abs_path) as savfile:
                data = json.load(savfile)  # data is load json
            self.obj_edit_f = data["3"][self.__magLensNames[0]]
            self.c1_edit_f = data["3"][self.__magLensNames[1]]
            self.c2_edit_f = data["3"][self.__magLensNames[2]]
            self.obj_stigmateur0_f=data["3"][self.__StigNames[0]]
            self.obj_stigmateur1_f=data["3"][self.__StigNames[1]]
            self.gun_stimateur0_f=data["3"][self.__StigNames[2]]
            self.gun_stigmateur1_f=data["3"][self.__StigNames[3]]
        except:
            logging.info('***LENSES***: No saved values.')

        self.obj_global_f = True
        self.c1_global_f = True
        self.c2_global_f = True

    def EHT_change(self, value):
        inst_dir = os.path.dirname(__file__)
        abs_path = os.path.join(inst_dir, 'lenses_settings.json')
        with open(abs_path) as savfile:
            data = json.load(savfile)  # data is load json
        self.obj_edit_f = data[str(value)][self.__magLensNames[0]]
        self.c1_edit_f = data[str(value)][self.__magLensNames[1]]
        self.c2_edit_f = data[str(value)][self.__magLensNames[2]]

    def get_values(self, which):
        cur, vol = self.__lenses_ps.locked_query(which)
        return cur, vol

    def shutdown_wobbler(self):
        self.obj_wobbler_f = False
        self.c1_wobbler_f = False
        self.c2_wobbler_f = False


    """
    WOBBLER GLOBAL SETTINGS
    """

    @property
    def wobbler_frequency_f(self):
        return self.__wobbler_frequency

    @wobbler_frequency_f.setter
    def wobbler_frequency_f(self, value):
        self.__wobbler_frequency = value
        self.shutdown_wobbler()
        self.property_changed_event.fire("wobbler_frequency_f")

    @property
    def wobbler_intensity_f(self):
        return self.__wobbler_intensity

    @wobbler_intensity_f.setter
    def wobbler_intensity_f(self, value):
        self.__wobbler_intensity = float(value)
        self.shutdown_wobbler()
        self.property_changed_event.fire("wobbler_intensity_f")

    """
    OBJECTIVE LENS
    """



    @property
    def obj_global_f(self):
        return self.__magLensGlobal[0]

    @obj_global_f.setter
    def obj_global_f(self, value):
        self.__magLensGlobal[0] = value
        if value:
            self.__lenses_ps.locked_set_val(self.__magLens[0], self.__magLensNames[0])
        else:
            self.__lenses_ps.locked_set_val(0.0, self.__magLensNames[0])
        self.property_changed_event.fire('obj_global_f')

    @property
    def obj_wobbler_f(self):
        return self.__magLensWobbler[0]

    @obj_wobbler_f.setter
    def obj_wobbler_f(self, value):
        self.__magLensWobbler[0] = value
        if value:
            self.__lenses_ps.wobbler_on(self.__magLens[0], self.__wobbler_intensity, self.__wobbler_frequency, self.__magLensNames[0])
        else:
            self.__lenses_ps.wobbler_off()
            self.obj_slider_f = self.__magLens[0] * 1e6
        self.property_changed_event.fire('obj_wobbler_f')

    @property
    def obj_slider_f(self):
        return int(self.__magLens[0] * 1e6)

    @obj_slider_f.setter
    def obj_slider_f(self, value):
        self.__magLens[0] = value / 1e6
        self.__lenses_ps.locked_set_val(self.__magLens[0], self.__magLensNames[0])
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")

    @property
    def obj_edit_f(self):
        return format(self.__magLens[0], '.6f')

    @obj_edit_f.setter
    def obj_edit_f(self, value):
        self.__magLens[0] = float(value)
        self.__lenses_ps.set_val(self.__magLens[0], self.__magLensNames[0])
        self.property_changed_event.fire("obj_slider_f")
        self.property_changed_event.fire("obj_edit_f")

    """
    CONDENSER 01
    """

    @property
    def c1_global_f(self):
        return self.__magLensGlobal[1]

    @c1_global_f.setter
    def c1_global_f(self, value):
        self.__magLensGlobal[1] = value
        if value:
            self.__lenses_ps.locked_set_val(self.__magLens[1], self.__magLensNames[1])
        else:
            self.__lenses_ps.locked_set_val(0.01, self.__magLensNames[1])
        self.property_changed_event.fire('c1_global_f')

    @property
    def c1_wobbler_f(self):
        return self.__magLensWobbler[1]

    @c1_wobbler_f.setter
    def c1_wobbler_f(self, value):
        self.__magLensWobbler[1] = value
        if value:
            self.__lenses_ps.wobbler_on(self.__magLens[1], self.__wobbler_intensity, self.__wobbler_frequency, self.__magLensNames[1])
        else:
            self.__lenses_ps.wobbler_off()
            self.c1_slider_f = self.__magLens[1] * 1e6
        self.property_changed_event.fire('c1_wobbler_f')

    @property
    def c1_slider_f(self):
        return int(self.__magLens[1] * 1e6)

    @c1_slider_f.setter
    def c1_slider_f(self, value):
        self.__magLens[1] = value / 1e6
        self.__lenses_ps.locked_set_val(self.__magLens[1], self.__magLensNames[1])
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    @property
    def c1_edit_f(self):
        return format(self.__magLens[1], '.6f')

    @c1_edit_f.setter
    def c1_edit_f(self, value):
        self.__magLens[1] = float(value)
        self.__lenses_ps.locked_set_val(self.__magLens[1], self.__magLensNames[1])
        self.property_changed_event.fire("c1_slider_f")
        self.property_changed_event.fire("c1_edit_f")

    """
    CONDENSER 02
    """

    @property
    def c2_global_f(self):
        return self.__magLensGlobal[2]

    @c2_global_f.setter
    def c2_global_f(self, value):
        self.__magLensGlobal[2] = value
        if value:
            self.__lenses_ps.locked_set_val(self.__magLens[2], self.__magLensNames[2])
        else:
            self.__lenses_ps.locked_set_val(0.01, self.__magLensNames[2])
        self.property_changed_event.fire('c2_global_f')

    @property
    def c2_wobbler_f(self):
        return self.__magLensWobbler[2]

    @c2_wobbler_f.setter
    def c2_wobbler_f(self, value):
        self.__magLensWobbler[2] = value
        if value:
            self.__lenses_ps.wobbler_on(self.__magLens[2], self.__wobbler_intensity, self.__wobbler_frequency, self.__magLensNames[2])
        else:
            self.__lenses_ps.wobbler_off()
            self.c2_slider_f = self.__magLens[2] * 1e6
        self.property_changed_event.fire('c2_wobbler_f')

    @property
    def c2_slider_f(self):
        return int(self.__magLens[2] * 1e6)

    @c2_slider_f.setter
    def c2_slider_f(self, value):
        self.__magLens[2] = value / 1e6
        self.__lenses_ps.locked_set_val(self.__magLens[2], self.__magLensNames[2])
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    @property
    def c2_edit_f(self):
        return format(self.__magLens[2], '.6f')

    @c2_edit_f.setter
    def c2_edit_f(self, value):
        self.__magLens[2] = float(value)
        self.__lenses_ps.locked_set_val(self.__magLens[2], self.__magLensNames[2])
        self.property_changed_event.fire("c2_slider_f")
        self.property_changed_event.fire("c2_edit_f")

    """
    STIGMATORS
    """

    @property
    def obj_stigmateur0_f(self):
        return self.__lenses_ps.query_stig(self.__StigNames[0])

    @obj_stigmateur0_f.setter
    def obj_stigmateur0_f(self, value):
        self.__Stig[0] = value
        self.__lenses_ps.set_val_stig(value, self.__StigNames[0])
        self.property_changed_event.fire('obj_stigmateur0_f')

    @property
    def obj_stigmateur1_f(self):
        return self.__lenses_ps.query_stig(self.__StigNames[1])

    @obj_stigmateur1_f.setter
    def obj_stigmateur1_f(self, value):
        self.__Stig[0] = value
        self.__lenses_ps.set_val_stig(value, self.__StigNames[1])
        self.property_changed_event.fire('obj_stigmateur1_f')

    @property
    def gun_stigmateur0_f(self):
        return self.__lenses_ps.query_stig(self.__StigNames[2])

    @gun_stigmateur0_f.setter
    def gun_stigmateur0_f(self, value):
        self.__lenses_ps.set_val_stig(value, self.__StigNames[2])
        self.property_changed_event.fire('gun_stigmateur0_f')

    @property
    def gun_stigmateur1_f(self):
        return self.__lenses_ps.query_stig(self.__StigNames[3])

    @gun_stigmateur1_f.setter
    def gun_stigmateur1_f(self, value):
        self.__lenses_ps.set_val_stig(value, self.__StigNames[3])
        self.property_changed_event.fire('gun_stigmateur1_f')