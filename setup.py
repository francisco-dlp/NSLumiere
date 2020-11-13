import setuptools

setuptools.setup(
    name="Lumiere Ultra Combo",
    version="4.2.2",
    author="Yves Auad",
    description="Lenses, EELS_Spec, Apertures,  Instrument",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=["nionswift_plugin.lenses", "nionswift_plugin.EELS_spec", "nionswift_plugin.diaf", "nionswift_plugin.IVG", "nionswift_plugin.stage", "nionswift_plugin.OptSpec"],
    python_requires='~=3.7',
    install_requires=["pyserial>=3.4"]
)
