from setuptools import setup

setup(
    name="OrsayLumiere",
    version="5.11.7",
    author="Yves Auad",
    description="Set of tools to run a VG Microscope in Nionswift",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=['nionswift_plugin.EELS_spec', 'nionswift_plugin.diaf',
              'nionswift_plugin.IVG', 'nionswift_plugin.IVG.virtual_instruments',
              'nionswift_plugin.IVG.tp3', 'nionswift_plugin.IVG.camera',
              'nionswift_plugin.IVG.scan', 'nionswift_plugin.lenses',
              'nionswift_plugin.OptSpec', 'nionswift_plugin.stage'],
    python_requires='>=3.8.5',
    data_files=[('nionswift_plugin/aux_files/config', [
        'nionswift_plugin/aux_files/config/Lumiere/global_settings.json',
        'nionswift_plugin/aux_files/config/Lumiere/diafs_settings.json',
        'nionswift_plugin/aux_files/config/Lumiere/eels_settings.json',
        'nionswift_plugin/aux_files/config/Lumiere/lenses_settings.json',
        'nionswift_plugin/aux_files/config/Lumiere/Orsay_cameras_list.json',

    ]), ('nionswift_plugin/aux_files/DLLs', [
        'nionswift_plugin/aux_files/DLLs/Cameras.dll',
        'nionswift_plugin/aux_files/DLLs/Scan.dll',
        'nionswift_plugin/aux_files/DLLs/udk3-1.4-x86_64.dll',
        'nionswift_plugin/aux_files/DLLs/udk3mod-1.4-winusb-x86_64.dll',
        'nionswift_plugin/aux_files/DLLs/STEMSerial.dll',
        'nionswift_plugin/aux_files/DLLs/Stepper.dll',
        'nionswift_plugin/aux_files/DLLs/delib64.dll',
        'nionswift_plugin/aux_files/DLLs/SpectroCL.dll',
        'nionswift_plugin/aux_files/DLLs/AttoClient.dll',
    ]), ('swift_rust/target/release', [
        'swift_rust/target/release/rust2swift.pyd'
    ]

    )],
    install_requires=["pyserial>=3.5", "requests>=2.25.1", "nionswift-usim>=0.3.0"]
)
