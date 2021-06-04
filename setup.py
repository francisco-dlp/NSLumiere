from setuptools import setup, find_packages

setup(
    name="OrsayLumiere",
    version="5.4.0",
    author="Yves Auad",
    description="Set of tools to run a VG Microscope in Nionswift",
    url="https://github.com/yvesauad/swift_lumiere",
    packages=find_packages(
        include=['nionswift_plugin.OptSpec',]),
    package_dir={"": "."},
    python_requires='~=3.8.5',
    install_requires=["pyserial>=3.5", "requests>=2.25.1"]
)
