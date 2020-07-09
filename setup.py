# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools

setuptools.setup(
    name="Lumiere Ultra Combo",
    version="2.13",
    author="Yves Auad",
    description="Lenses, EELS_Spec, Apertures,  Instrument",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=["nionswift_plugin.lenses", "nionswift_plugin.EELS_spec", "nionswift_plugin.diaf", "nionswift_plugin.IVG", "nionswift_plugin.stage", "nionswift_plugin.Scan_Lum"],
    python_requires='~=3.7',
)

#dependencies = pip install pyvisa and pip install pyvisa-py and pip install pyusb
