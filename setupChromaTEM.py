from setuptools import setup

setup(
    name="OrsayChromaTEM",
    version="1.0",
    author="Yves Auad",
    description="Set of tools to run a VG Microscope in Nionswift",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=['nionswift_plugin.OptSpec'],
    python_requires='>=3.8.5',
    data_files=[('nionswift_plugin/aux_files/config', [
        'nionswift_plugin/aux_files/config/ChromaTEM/global_settings.json',
        'nionswift_plugin/aux_files/read_data.py'
    ]), ('nionswift_plugin/aux_files/DLLs', [
        'nionswift_plugin/aux_files/DLLs/SpectroCL.dll',
        'nionswift_plugin/aux_files/DLLs/AttoClient.dll',
    ]
    )]
)
