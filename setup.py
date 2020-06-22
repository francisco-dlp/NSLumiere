# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools
import os

setuptools.setup(
    name="Lumiere Ultra Combo",
    version="1.2",
    author="Yves Auad",
    description="Lenses",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=["nionswift_plugin.lenses", "nionswift_plugin.EELS_spec"],
    python_requires='~=3.6',
)

#dependencies = pip install pyvisa and pip install pyvisa-py and pip install pyusb
