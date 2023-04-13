import numpy

from nion.typeshed import Interactive_1_0 as Interactive
from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI


class MaskCreator():

    def __init__(self, data_item):
        self.graphics = dict()
        self.data_item = data_item
        self.data_shape = (data_item.data.shape[0], data_item.data.shape[1])
        self.masks_serial = numpy.array([], dtype=numpy.int16)

    def create_bf(self):
        graphic = self.graphics['BF']
        center = [(a*b)%256 for (a, b) in zip(graphic.center, self.data_shape)]
        radius = [(a*b / 2)%256 for (a, b) in zip(graphic.size, self.data_shape)]
        print(f'Creating BF mask. Center is {center} and radius is {radius}.')
        self.__create_round_mask(center, radius, 0, 1)

    def create_adf(self):
        graphic = self.graphics['ADF']
        center = [(a*b)%256 for (a, b) in zip(graphic.center, self.data_shape)]
        radius = [(a*b / 2)%256 for (a, b) in zip(graphic.size, self.data_shape)]
        print(f'Creating ADF mask. Center is {center} and radius is {radius}.')
        self.__create_round_mask(center, radius, 1, 0)

    def reset_masks(self):
        self.masks_serial = numpy.array([], dtype=numpy.int16)

    def create_dual_graphics(self):
        data_shape = self.data_item.data.shape
        uniform_array = numpy.arange(0, data_shape[1], 1)
        xarray = numpy.sum(self.data_item.data, axis=0)
        xaverage = numpy.average(uniform_array, weights=xarray)
        xvariance = numpy.average((uniform_array - xaverage) ** 2, weights=xarray)

        uniform_array = numpy.arange(0, data_shape[0], 1)
        yarray = numpy.sum(self.data_item.data, axis=1)
        yaverage = numpy.average(uniform_array, weights=yarray)
        yvariance = numpy.average((uniform_array - yaverage) ** 2, weights=yarray)

        center = (xaverage / data_shape[1], yaverage / data_shape[0])
        radius_bf = (3.0 * numpy.sqrt(xvariance) / data_shape[1], 3.0 * numpy.sqrt(yvariance) / data_shape[0])
        radius_adf = (4.0 * numpy.sqrt(xvariance) / data_shape[1], 4.0 * numpy.sqrt(yvariance) / data_shape[0])

        circle = self.data_item.add_ellipse_region(center[1], center[0], radius_bf[1], radius_bf[0])
        circle.label = 'BF'
        self.graphics['BF'] = circle

        circle2 = self.data_item.add_ellipse_region(center[1], center[0], radius_adf[1], radius_adf[0])
        circle2.label = 'ADF'
        self.graphics['ADF'] = circle2

    def __create_round_mask(self, center, radius, initial, value):
        mask = numpy.zeros(256 * 256, dtype=numpy.int16)
        mask[:] = initial
        for x in range(256):
            for y in range(256):
                if ((x - center[1]) / radius[1]) ** 2 + ((y - center[0]) / radius[0]) ** 2 < 1:
                    mask[y * 256 + x] = value
        self.masks_serial = numpy.append(self.masks_serial, mask)

    def output_values(self):
        print(f'Mask is written to file. Size is {self.masks_serial.shape}.')
        self.masks_serial.tofile("C:\\ProgramData\\Microscope\\masks.dat")

def do_task(interactive: Interactive, api: API):
    target_data_item = api.application.document_windows[0].target_data_item
    mask_obj = MaskCreator(target_data_item)
    mask_obj.create_dual_graphics()
    mask_obj.create_bf()
    mask_obj.create_adf()
    mask_obj.output_values()
    while True:
        is_confirmed = interactive.confirm_yes_no('Update 4D Mask')
        if is_confirmed:
            mask_obj.reset_masks()
            mask_obj.create_bf()
            mask_obj.create_adf()
            mask_obj.output_values()
        else:
            break

def script_main(api_broker):
    interactive = api_broker.get_interactive(Interactive.version)  # type: Interactive
    api = api_broker.get_api(API.version, UI.version)  # type: API
    do_task(interactive, api)

"""
api = api_broker.get_api(API.version, UI.version)  # type: API

window = api.application.document_windows[0]
data_item = window.target_data_item
data_shape = data_item.data.shape

uniform_array = numpy.arange(0, data_shape[1], 1)
xarray = numpy.sum(data_item.data, axis = 0)
xaverage = numpy.average(uniform_array, weights=xarray)
xvariance = numpy.average((uniform_array-xaverage)**2, weights=xarray)

uniform_array = numpy.arange(0, data_shape[0], 1)
yarray = numpy.sum(data_item.data, axis = 1)
yaverage = numpy.average(uniform_array, weights=yarray)
yvariance = numpy.average((uniform_array-yaverage)**2, weights=yarray)

center = (xaverage / data_shape[1], yaverage / data_shape[0])
radius_bf = (3.0 * numpy.sqrt(xvariance) / data_shape[1], 3.0 * numpy.sqrt(yvariance) / data_shape[0])
radius_adf = (4.0 * numpy.sqrt(xvariance) / data_shape[1], 4.0 * numpy.sqrt(yvariance) / data_shape[0])

circle = data_item.add_ellipse_region(center[1], center[0], radius_bf[1], radius_bf[0])
circle.label = 'BF'

circle2 = data_item.add_ellipse_region(center[1], center[0], radius_adf[1], radius_adf[0])
circle2.label = 'ADF'

#circle = data_item.add_ellipse_region(center[1], center[0], radius[1], radius[0])
#circle.label = 'ADF'


#uniform_array = numpy.ones((256, 1025))
#average = numpy.average(uniform_array, weights=data_item.data, axis = 1)
#print(average)

#mean = numpy.mean(data_item.data, axis = 0)
#print(data_item.data)
#mean1 = numpy.mean(numpy.sum(data_item.data, axis = 0))
#mean2 = numpy.mean(numpy.sum(data_item.data, axis = 1))
#print(mean1)
#print(mean2)

#for graphics in data_item.graphics:
#    if graphics.label == "ADF":
#        assert graphics.graphic_type == "ellipse-graphic"
#        center = [int(val1 * val2) for (val1, val2) in zip(data_shape, graphics.center)]
#        radius = [int(val1 * val2) for (val1, val2) in zip(data_shape, graphics.size)]
"""