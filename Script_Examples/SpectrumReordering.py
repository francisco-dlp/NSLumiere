from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.typeshed import Interactive_1_0 as Interactive
import nionswift_plugin.orsay_suite.orsay_data as OD
import numpy

#Hyperspy import for Typing
from hyperspy._signals.signal1d import Signal1D

def script_main(api_broker):
    interactive: Interactive.Interactive = api_broker.get_interactive(Interactive.version)
    api = api_broker.get_api(API.version, UI.version)  # type: API
    window = api.application.document_windows[0]

    ### Getting the DataItem ###
    data_item: API.DataItem = window.target_data_item
    data_shape = data_item.data.shape
    prod_data_shape = numpy.prod(data_shape)
    metadata = data_item.metadata
    title = data_item.title
    try:
        decode_list = metadata['scan']['scan_device_properties']['decode_list']
    except KeyError:
        decode_list = metadata['hardware_source']['decode_list']
    decode_list = numpy.array(decode_list, dtype='int')

    ### Getting a hyperspy object ###
    """
    wrapper data is the entire object. It has the Nionswift DataItem + the Hspy Object
    hspy_data is only the hspy data. You are going to modify/replace this data
    """
    wrapper_data: OD.HspySignal1D = OD.HspySignal1D(data_item)
    hspy_data:  Signal1D = wrapper_data.hspy_gd
    hspy_data.data = hspy_data.data.reshape((decode_list.size, prod_data_shape//decode_list.size))[decode_list].reshape(data_shape)

    ### Getting a calibrated DataItem back ###
    """
    wrapper data is used to recover everything from the initial unmodified DataItem (metadata + caption + calibration, etc)
    """
    data_and_metadata = wrapper_data.get_data_and_metadata(hspy_data)
    new_data_item: API.DataItem = api.library.create_data_item_from_data_and_metadata(data_and_metadata, "ReOrderedArray_" + title)
    api.application.document_windows[0].display_data_item(new_data_item)