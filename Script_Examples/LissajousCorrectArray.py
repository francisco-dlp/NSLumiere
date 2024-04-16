from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.typeshed import Interactive_1_0 as Interactive
import nionswift_plugin.orsay_suite.orsay_data as OD
import numpy
import cv2

#Hyperspy import for Typing
from hyperspy._signals.signal1d import Signal1D

DACX_BITDEPTH = 14
DACY_BITDEPTH = 14
FILTER_INTENSITY = 49
NUMBER_OF_IMAGES = 50


def rebin(arr, new_shape):
    shape = (new_shape[0], arr.shape[0] // new_shape[0], new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)

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
    intensity_calibration = data_item.intensity_calibration
    dimensional_calibration = data_item.dimensional_calibrations
    dimensional_calibration_new = api.create_calibration(0.0, 1.0, 'us')
    dimensional_calibration.insert(0, dimensional_calibration_new)

    #Getting relevant metadata
    xmax, ymax = metadata['scan']['scan_size']
    lissajous_nx = metadata['scan']['scan_device_properties']['lissajous_nx']
    lissajous_ny = metadata['scan']['scan_device_properties']['lissajous_ny']
    lissajous_phase = metadata['scan']['scan_device_properties']['lissajous_phase']
    pixel_time = metadata['scan']['scan_device_parameters']['pixel_time_us'] / 1e6 * 1e8

    #Calculating the points
    offset = numpy.pi * float(lissajous_phase)
    nx = float(lissajous_nx)
    ny = float(lissajous_ny)
    freqx = int(xmax * ymax * pixel_time * 1e-8 * nx)
    freqy = int(xmax * ymax * pixel_time * 1e-8 * ny)
    print(f"Number of forward-backward in X and Y directions are {freqx} and {freqy}.")
    x = numpy.linspace(offset, freqx * numpy.pi * 2 + offset, xmax * ymax)
    y = numpy.linspace(0, freqy * numpy.pi * 2, ymax * ymax)
    x_flatten = ((numpy.sin(x) / 2 + 0.5) * ((1 << DACX_BITDEPTH) - 1)).astype('uint64')
    y_flatten = ((numpy.sin(y) / 2 + 0.5) * ((1 << DACX_BITDEPTH) - 1)).astype('uint64')

    # Getting the correct array
    initial_point = 0
    step = int(xmax * ymax / NUMBER_OF_IMAGES)
    FullCompleteImage = numpy.zeros((NUMBER_OF_IMAGES, xmax, ymax) , dtype='int32')
    for index in range(NUMBER_OF_IMAGES):
        print(f"Current image is {index}.")
        orderedArrayRaw = (y_flatten * (1 << DACX_BITDEPTH) + x_flatten)[initial_point + step * index : step * (index + 1)]
        completeImage = numpy.zeros((1<<14)**2 , dtype='int32')
        completeImage[orderedArrayRaw] = data_item.data.ravel()[initial_point + step * index : step * (index + 1)]
        completeImage = rebin(numpy.reshape(completeImage, (1 << DACY_BITDEPTH, 1 << DACY_BITDEPTH)),
                              ((ymax, xmax))).astype('float32')
        completeImage = cv2.GaussianBlur(completeImage, (FILTER_INTENSITY, FILTER_INTENSITY), 0)
        FullCompleteImage[index, :, :] = completeImage

    data_descriptor = api.create_data_descriptor(is_sequence=True, collection_dimension_count=0,
                                                 datum_dimension_count=2)
    xdata = api.create_data_and_metadata(FullCompleteImage, intensity_calibration=intensity_calibration,
                                         dimensional_calibrations=dimensional_calibration,
                                         metadata=metadata, data_descriptor=data_descriptor)
    api.library.create_data_item_from_data_and_metadata(xdata, "Processed_"+title)


