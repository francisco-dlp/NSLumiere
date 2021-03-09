import numpy
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API


slice = numpy.fromfile('C:\\Users\\AUAD\\Documents\\Tp3_tools\\rusty_tcp\\src\\slice2.dat', dtype='uint8')

height = 128
width = 128

dt = numpy.dtype(numpy.uint32).newbyteorder('>')
frame_int = numpy.frombuffer(slice, dtype=dt)
frame_int = numpy.reshape(frame_int, (height, width, 1024))

si_data_descriptor = api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=1)
si_xdata = api.create_data_and_metadata(frame_int, data_descriptor=si_data_descriptor)
data_item = api.library.create_data_item_from_data_and_metadata(si_xdata)