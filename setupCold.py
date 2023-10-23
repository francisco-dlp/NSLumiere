from setuptools import setup

setup(
    name="OrsayCold",
    version="10.6.4",
    author="Yves Auad",
    description="Set of tools to run VG Cold Microscope in Nionswift",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=['nionswift_plugin.EELS_spec',
              'nionswift_plugin.IVG', 'nionswift_plugin.IVG.virtual_instruments',
              'nionswift_plugin.IVG.tp3', 'nionswift_plugin.IVG.camera',
              'nionswift_plugin.IVG.scan', 'nionswift_plugin.OptSpec',
              'nionswift_plugin.lenses', 'nionswift_plugin.stage'],
    python_requires='>=3.8.5',
    data_files=[('nionswift_plugin/aux_files/config', [
        'nionswift_plugin/aux_files/config/Cold/global_settings.json',
        'nionswift_plugin/aux_files/config/Cold/eels_settings.json',
        'nionswift_plugin/aux_files/config/Cold/lenses_settings.json',
        'nionswift_plugin/aux_files/config/Cold/Orsay_cameras_list.json',
        'nionswift_plugin/aux_files/config/Debug/stage_settings.json',
        'nionswift_plugin/aux_files/read_data.py'

    ]), ('nionswift_plugin/aux_files/DLLs', [
        'nionswift_plugin/aux_files/DLLs/Cameras.dll',
        'nionswift_plugin/aux_files/DLLs/atmcd64d.dll',
        'nionswift_plugin/aux_files/DLLs/Scan.dll',
        'nionswift_plugin/aux_files/DLLs/Connection.dll',
        'nionswift_plugin/aux_files/DLLs/Connection.dll.config',
        'nionswift_plugin/aux_files/DLLs/STEMSerial.dll',
        'nionswift_plugin/aux_files/DLLs/Stepper.dll',
        'nionswift_plugin/aux_files/DLLs/delib64.dll',
        'nionswift_plugin/aux_files/DLLs/SpectroCL.dll',
        'nionswift_plugin/aux_files/DLLs/AttoClient.dll',
    ]

    )],
    zip_safe = False
)
