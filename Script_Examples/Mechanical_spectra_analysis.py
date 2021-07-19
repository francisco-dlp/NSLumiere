import numpy
import uuid
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI

api = api_broker.get_api(API.version, UI.version)  # type: API
DI = api.library.get_data_item_by_uuid(uuid.UUID("fcd81687-234e-4014-b01c-5e1e8aa4b11e"))

print(f'Data Item title is {DI.title}')
print(f'Data item has shape of {DI.data.shape}')
print(dir(api.library))

def dist(val1, val2):
    return numpy.sum(numpy.power(numpy.subtract(val1, val2), 2))**(0.5)

x, y, pixels = DI.data.shape
sumval = numpy.zeros((x, y))
for xpos in range(x):
    print('1st Part: Done '+format(100*xpos/x, '.1f')+' %')
    for ypos in range(y):
        spec = DI.data[xpos, ypos]
        spec = numpy.subtract(spec, spec.min())
        sumval[xpos, ypos] = numpy.sum(spec[775:825])

sumval = numpy.divide(sumval, sumval.max())
xmax, ymax = numpy.where(sumval==1)
xmax=xmax[0]
ymax=ymax[0]
maxpos = numpy.where(sumval==1)

dimensional_calibrations = DI.dimensional_calibrations[:-1]
xdata = api.create_data_and_metadata(sumval,
                                     dimensional_calibrations=dimensional_calibrations)
data_item = api.library.create_data_item_from_data_and_metadata(xdata)
data_item.title = '**SCRIPTED**'+DI.title

d = numpy.zeros(x)
d[1]+=1
for xpos in range(x):
    print('2nd Part: Done '+format(100*xpos/x, '.1f')+' %')
    for ypos in range(y):
        index = round(dist([xpos, ypos], [xmax, ymax]))
        d[index]+=sumval[xpos, ypos] / (dist([xpos, ypos], [xmax, ymax])+1.0)

xdata02 = api.create_data_and_metadata(d[1:])
data_item = api.library.create_data_item_from_data_and_metadata(xdata02)
data_item.title = '**SCRIPTED_PD**'+DI.title