import gettext
import logging

from nion.utils import Converter
from nion.utils import Model
from nion.utils import Registry

from . import tp3_camera

_ = gettext.gettext


class CameraHandler:
    """Handle interaction between the user interface and the hardware.

    This class should respond to changes from the UI by controlling the hardware. Conversely, it should respond to
    changes from the hardware by updating the UI. Some care should be given to avoiding UI loops.
    """

    # these variables will be filled in when the UI view is constructed.
    cancel_button = None
    stop_button = None
    start_button = None

    # models used

    def __init__(self, api, event_loop, ui_view, hardware_source_id, camera_device: tp3_camera.Camera,
                 camera_settings: tp3_camera.CameraSettings):
        self.event_loop = event_loop
        self.ui_view = ui_view

        self.hardware_source = api.get_hardware_source_by_id(hardware_source_id, "~1.0")
        self.__hardware_source = self.hardware_source._hardware_source
        self.camera_device = camera_device
        self.camera_settings = camera_settings

        print(camera_device)
        print('oioioioioi')

    def init_handler(self):
        """Initialize the UI after it has been constructed."""
        self.event_loop.create_task(self.update_buttons())

    def cancel_clicked(self, widget):
        """Handle cancel button click.

        This method is called when the user clicks on the button. The name of this method corresponds to the
        `on_clicked` property of the push button."""
        self.hardware_source.abort_playing()

    def stop_clicked(self, widget=None):
        """Handle stop button click.

        This method is called when the user clicks on the button. The name of this method corresponds to the
        `on_clicked` property of the push button."""
        self.hardware_source.stop_playing()

    def start_clicked(self, widget):
        """Handle start button click.

        This method is called when the user clicks on the button. The name of this method corresponds to the
        `on_clicked` property of the push button."""
        # print(f"At start exposure = {self.exposure_model.value}")
        self.hardware_source.start_playing()

    async def update_buttons(self):
        is_playing = self.hardware_source.is_playing
        self.cancel_button.enabled = is_playing
        self.stop_button.enabled = is_playing
        self.start_button.enabled = not is_playing
        self.status_text.value = "Running" if is_playing else "Stopped"

    def __acquisition_state_changed(self, is_acquiring):
        # this message will come from a thread. use event loop to call functions on the main thread.
        self.event_loop.create_task(self.update_buttons())


class CameraPanelFactory:
    camera_panel_type = "tp3_camera_panel"

    def get_ui_handler(self, api_broker=None, event_loop=None, hardware_source_id=None,
                       camera_device=None, camera_settings=None, **kwargs):
        ui_view = self.__create_ui_view(api_broker.get_ui("~1.0"), camera_device)
        api = api_broker.get_api("~1.0")
        return CameraHandler(api, event_loop, ui_view, hardware_source_id, camera_device, camera_settings)

    def __create_ui_view(self, ui, camera_device) -> dict:
        """Creates the UI view by using the declarative UI library.

        The UI view is simply a Python dictionary, constructed with the help of the declarative UI library."""
        self.controller_label = ui.create_label(name='controller_label', text='Controller: ')

        tabs_column = ui.create_column(self.controller_label)

        return tabs_column

def run():
    camera_panel_factory = CameraPanelFactory()
    Registry.register_component(camera_panel_factory, {"camera_panel"})
