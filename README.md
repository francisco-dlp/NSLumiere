

# VG Lumiere Swift
Welcome to swift_lumiere. This repo includes the developments in order to run an old VG Microscope in the NionSwift software. For reference, VG Lumiere @ Orsay is/was used for dev.

# Installing

We have tested this version extensively in Nion Swift 0.15.6. Rust libraries are being used experimentally, but requires
python <3.9 in order to run. If you wish to explore rust libraries, install nionswift as follows:

`conda create -n nionswift -c nion nionswift==0.15.6 nionswift-tool python==3.8.8`

Proceed to our module installation. Clone master branch or most up-to-date development branch using:

`git clone https://github.com/yvesauad/swift_lumiere.git`

Inside your nionswift environment, if you are using anaconda/miniconda, install locally using 

`python setupLum.py clean --all install`

or `python setupCold.py clean --all install`

or `python setupChromaTEM.py clean --all install`

Depending on the microscope you wish to Install. Any custom microscope can be easily built creating a new setup file.


# Troubleshoot

Will be updated soon.


## Known Issues

All known issues have been resolved.

# Found a bug? Report to us!

Have you found a bug in the software? Plugin could not be installed in your machine? Please report all bug to us.
