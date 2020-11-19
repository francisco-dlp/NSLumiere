import numpy
import uuid
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API
DI = api.library.get_data_item_by_uuid(uuid.UUID("0900f18a-e8f7-40a8-ab87-8f5b70a8a771"))

print(f'Data Item title is {DI.title}')
print(f'Data item has shape of {DI.data.shape}')

x, y, pixels = DI.data.shape
minval = numpy.zeros((x, y))
maxval = numpy.zeros((x, y))
for xpos in range(x):
    print('Done '+format(100*xpos/x, '.1f')+' %')
    for ypos in range(y):
        spec = DI.data[xpos, ypos]
        minval[xpos, ypos], maxval[xpos, ypos] = min(spec[750:850]), max(spec[750:850])


maxval = numpy.subtract(maxval, minval)
maxval = numpy.divide(maxval, maxval.max())


dimensional_calibrations = DI.dimensional_calibrations[:-1]
xdata = api.create_data_and_metadata(maxval,
                                     dimensional_calibrations=dimensional_calibrations)
data_item = api.library.create_data_item_from_data_and_metadata(xdata)
data_item.title = '**SCRIPTED**'+DI.title