import numpy
import uuid
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API
DI = api.library.get_data_item_by_uuid(uuid.UUID("de1e1c89-55d1-43c4-ba2f-eeb5a0d6446c"))

print(f'Data Item title is {DI.title}')
print(f'Data item has shape of {DI.data.shape}')

x, y, pixels = DI.data.shape
minval = numpy.zeros((x, y))
maxval = numpy.zeros((x, y))
for xpos in range(x):
    print('Done '+format(100*xpos/x, '.1f')+' %')
    for ypos in range(y):
        spec = DI.data[xpos, ypos]
        minval[xpos, ypos], maxval[xpos, ypos] = min(spec), max(spec)

print(minval)
print(numpy.average(minval))