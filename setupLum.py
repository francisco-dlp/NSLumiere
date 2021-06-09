from setuptools import setup, find_packages

setup(
    name="OrsayLumiere",
    version="5.6.0",
    author="Yves Auad",
    description="Set of tools to run a VG Microscope in Nionswift",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=['nionswift_plugin', 'nionswift_plugin.diaf', 'nionswift_plugin.EELS_spec',
              'nionswift_plugin.IVG', 'nionswift_plugin.lenses',
              'nionswift_plugin.OptSpec', 'nionswift_plugin.stage'],
    python_requires='>=3.8.5',
    install_requires=["pyserial>=3.5", "requests>=2.25.1", "nionswift-usim>=0.3.0"]
)
