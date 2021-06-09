

# VG Lumiere Swift
Welcome to swift_lumiere. This repo includes the developments in order to run an old VG Microscope in the NionSwift software. For reference, VG Lumiere @ Orsay is/was used for dev.

# Installing
Clone master branch or most up-to-date development branch using:

`git clone https://github.com/yvesauad/swift_lumiere.git`

Inside your nionswift environment, if you are using anaconda/miniconda, install locally using 

`python setupLum.py clean --all install`

or `python setupCold.py clean --all install`

or `python setupChromaTEM.py clean --all install`

or `python setupVirtual.py clean --all install`

Depending on the microscope you wish to Install. Any custom microscope can be easily built creating a new setup file.

All required packages will be automatically installed. In this case, we use pyserial for controlling all our serial instruments. Apertures, EELS Spectrometer, Lenses (C1, C2 and OBJ), gauges are a few examples of this instrument list.

# Troubleshoot

Inside our nionswift_plugin folder, there is a `global_setting.json` variable which defines all constants for each microscope run. If you experience bugs or issues that you can not identify, please put all `DEBUG=1`. If you stil experiencing problems, turn of `FAST_PERIODIC` and `SLOW_PERIODIC`. They are Thread.Timer which handles communication with other instruments. `DEBUG=1` alone is tested with no microscope hardware at all under Ubuntu 18.01 and Windows 10.

All instruments have a hardware controlled file and a virtual one. If you obtain Serial errors during an attempt of opening Nionswift, please put everything in DEBUG mode and run again. Search for callback message which always follows the format `***MY_INSTRUMENT***: MY_MESSAGE`. They are present in all serial communication errors and will show up in that case.

In case of persistence of errors, check if all libraries were properly installed using `pip list` or `conda list`. Remember pyserial library uses `import serial`. Our package will show up as [Lumiere_Ultra_Combo.]

## Known Issues

a) Both Thread.Timer displays error messages in the attempt of closing nionswift or changing library. Altough annoying, this is not supossed to affect any functionality of the microscope.

b) Stepper.dll must be in the same path of the executor file for the stage. There is a init message ***VG STAGE*** showing the correct path of the current executable. Stepper.dll file is inside stage module and produces no effect in stage folder. Stepper.dll is used together with ctypes to use native library of the VG Stepper Motor.


# Found a bug? Report to us!

Have you found a bug in the software? Plugin could not be installed in your machine? Please report all bug to us.
