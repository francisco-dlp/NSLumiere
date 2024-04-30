from nion.typeshed import API_1_0 as API
from nion.typeshed import UI_1_0 as UI
from nion.typeshed import Interactive_1_0 as Interactive
from scipy import signal
from scipy.interpolate import griddata
import numpy
import cv2

DACX_BITDEPTH = 14
DACY_BITDEPTH = 14
NUMBER_OF_IMAGES = 1
SAWTOOTH = False


def rebin(arr, new_shape):
    shape = (new_shape[0], arr.shape[0] // new_shape[0], new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)


# Define a function 'gcd' to calculate the greatest common divisor (GCD) of two positive integers.
def gcd(p, q):
    # Use Euclid's algorithm to find the GCD.
    while q != 0:
        p, q = q, p % q
    return p


# Define a function 'is_coprime' to check if two numbers are coprime (GCD is 1).
def is_coprime(x, y):
    # Check if the GCD of 'x' and 'y' is equal to 1.
    return gcd(x, y) == 1

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
    mean = numpy.mean(data_item.data)

    #Getting relevant metadata
    xmax, ymax = metadata['scan']['scan_size']
    lissajous_nx = metadata['scan']['scan_device_properties']['lissajous_nx']
    lissajous_ratio = metadata['scan']['scan_device_properties']['lissajous_ratio']
    lissajous_phase = metadata['scan']['scan_device_properties']['lissajous_phase']
    pixel_time = metadata['scan']['scan_device_parameters']['pixel_time_us']
    pixel_time = int(pixel_time / 0.01) - int(int(pixel_time / 0.01) % 4)

    divider = 2

    #Calculating the points
    freqx = int(xmax * ymax * pixel_time * 1e-8 * lissajous_nx)
    freqy = int(xmax * ymax * pixel_time * 1e-8 * lissajous_nx * lissajous_ratio)
    offset = numpy.pi * float(lissajous_phase) / (4 * freqx)
    for index in range(10):
        if is_coprime(freqx, freqy): break
        print(f"***Device Library***: Not co-primes. Trying again {index}...")
        freqy -= 1
    print(f"***Device Library***: Number of forward-backward in X and Y directions are {freqx} and {freqy}. They are coprimes: {is_coprime(freqx, freqy)}.")
    x = numpy.linspace(0, freqx * numpy.pi * 2, xmax * ymax)
    y = numpy.linspace(offset, freqy * numpy.pi * 2 + offset, xmax * ymax)
    if not SAWTOOTH:
        x_flatten = (numpy.sin(x) / 2 + 0.5)
        y_flatten = (numpy.sin(y) / 2 + 0.5)
    else:
        x_flatten = (signal.sawtooth(x, 0.5) / 2 + 0.5)
        y_flatten = (signal.sawtooth(y, 0.5) / 2 + 0.5)

    # Getting the correct array
    initial_point = 0
    step = int(xmax * ymax / NUMBER_OF_IMAGES)
    FullCompleteImage_0 = numpy.zeros((NUMBER_OF_IMAGES, xmax>>divider, ymax>>divider) , dtype='float32')
    full_image = data_item.data.ravel()
    for index in range(NUMBER_OF_IMAGES):
        print(f"Current image is {index}.")

        image = full_image[initial_point + step * index: step * (index + 1)]
        grid_x, grid_y = numpy.mgrid[0:1:complex(xmax>>divider), 0:1:complex(ymax>>divider)]
        points = numpy.array([y_flatten[initial_point + step * index : step * (index + 1)], x_flatten[initial_point + step * index : step * (index + 1)]]).T
        print(f"Interpolating....")
        grid_z0 = griddata(points, image, (grid_x, grid_y), method='nearest', fill_value=-4096).astype('float32')

        FullCompleteImage_0[index, :, :] += grid_z0

    data_descriptor = api.create_data_descriptor(is_sequence=True, collection_dimension_count=0,
                                                 datum_dimension_count=2)
    xdata_0 = api.create_data_and_metadata(FullCompleteImage_0, intensity_calibration=intensity_calibration,
                                         dimensional_calibrations=dimensional_calibration,
                                         metadata=metadata, data_descriptor=data_descriptor)
    api.library.create_data_item_from_data_and_metadata(xdata_0, "Interp_Processed_0_"+title)


