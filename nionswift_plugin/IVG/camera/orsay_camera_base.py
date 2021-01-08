import abc


class Orsay_Camera_Base(abc.ABC):
    """
    defines functions required in all orsay cameras
    """
    
    def registerLogger(self, fn) -> None:
        """
        Replaces the original logger function
        """
        pass

    def addConnectionListener(self, fn) -> None:
        """
        function called when connection state changes
        """
        pass

    @property
    def simulation_mode(self) -> bool:
        """
        Tell if camera is in simulation mode
        Useful for spectrum imaging simulation
        """
        return False

    @abc.abstractmethod
    def getImageSize(self) -> int:
        """
        Read size of image given by the current setting
        """
        ...
           
    @abc.abstractmethod
    def getCCDSize(self) -> (int, int):
        """
        Size of the camera ccd chip
        """
        ...

    @abc.abstractmethod
    def registerDataLocker(self, fn):
        """"
        Function called to get data storage for a frame by frame readout
        """
        ...

    @abc.abstractmethod
    def registerDataUnlocker(self, fn):
        """
        Function called when data process is done for a frame by frame readout
        """
        ...

    @abc.abstractmethod
    def registerSpimDataLocker(self, fn):
        """
        Function called to get data storage for a spectrum image readout
        """
        ...

    @abc.abstractmethod
    def registerSpimDataUnlocker(self, fn):
        """
        Function called when data process is done for a spectrum image readout
        """
        ...

    @abc.abstractmethod
    def registerSpectrumDataLocker(self, fn):
        """
        Function called to get data storage for the current spectrum in spim readout
        """
        ...

    @abc.abstractmethod
    def registerSpectrumDataUnlocker(self, fn):
        """
        Function called when data process is done he current spectrum in spim readout
        """
        ...

    def setCCDOverscan(self, sx: int, sy: int):
        """
        For roper CCD cameras changes the size of the chip artificially to do online baseline correction (should 0,0 or 128,0)
        """
        pass

    def displayOverscan(self, displayed: bool):
        """
        When displayed set, the overscan area is displayed, changing image/spectrum size
        """
        pass

    @abc.abstractmethod
    def getBinning(self):
        """
        Return horizontal, vertical binning
        """
        ...

    @abc.abstractmethod
    def setBinning(self, bx: int, by: int):
        """
        Set  horizontal, vertical binning
        """
        ...

    @abc.abstractmethod
    def setMirror(self, mirror):
        """
        If mirror true, horizontal data are flipped
        """
        ...

    @abc.abstractmethod
    def setAccumulationNumber(self, count: int):
        """
        Define the number of images/spectra to sum (change to a property?
        """
        ...

    @abc.abstractmethod
    def getAccumulateNumber(self):
        """
        Return the number of images/spectra to sum (change to a property?
        """
        ...

    @abc.abstractmethod
    def setSpimMode(self, mode):
        """
        Set the spim operating mode: 0:SPIMSTOPPED, 1:SPIMRUNNING, 2:SPIMPAUSED, 3:SPIMSTOPEOL, 4:SPIMSTOPEOF, 5:SPIMONLINE
        """
        ...

    @abc.abstractmethod
    def startSpim(self, nbspectra, nbspectraperpixel, dwelltime, is2D):
        """
        Start spectrum imaging acquisition
        """
        ...

    @abc.abstractmethod
    def pauseSpim(self):
        """
        Pause spectrum imaging acquisition no tested yet
        """
        ...

    @abc.abstractmethod
    def resumeSpim(self, mode):
        """
        Resume spectrum imaging acquisition with mode: 0:SPIMSTOPPED, 1:SPIMRUNNING, 2:SPIMPAUSED, 3:SPIMSTOPEOL, 4:SPIMSTOPEOF, 5:SPIMONLINE
        """
        ...

    @abc.abstractmethod
    def stopSpim(self, immediate):
        ...

    @abc.abstractmethod
    def isCameraThere(self):
        """
        Check if the camera exists
        """
        ...

    def getTemperature(self):
        """
        Read ccd temperature and locked status
        """
        return 20

    def setTemperature(self, temperature):
        """
        Set the ccd temperature target point
        """
        pass

    @abc.abstractmethod
    def setupBinning(self):
        """
        Adjust binning using all current parameters and load it to camera
        """
        ...

    @abc.abstractmethod
    def startFocus(self, exposure, displaymode, accumulate):
        """
        Start imaging display mode: 1d, 2d  accumulate if images/spectra have to be summed
        """
        ...

    @abc.abstractmethod
    def stopFocus(self):
        """
        Stop imaging
        """
        ...

    @abc.abstractmethod
    def setExposureTime(self, exposure):
        """
        Defines exposure time, usefull to get then frame rate including readout time
        """
        ...

    def getNumofSpeeds(self, cameraport):
        """
        Find the number of speeds available for a specific readout port, they can be port dependant on some cameras
        """
        return 0

    def getSpeeds(self, cameraport):
        """
        Return the list of speeds for the cameraport as strings
        """
        speeds = list()
        return speeds

    def getCurrentSpeed(self, cameraport):
        """
        Find the speed used
        """
        return 0

    def getAllPortsParams(self):
        """
        Find the list of speeds for all ports return a tuple of (port name, (speeds,), (gains,)
        """
        allportsparams = ()
        return allportsparams

    def setSpeed(self, cameraport, speed):
        """
        Select speed used on this port
        """
        return True

    def getNumofGains(self, cameraport):
        """
        Find the number of gains available for a specific readout port, they can be port dependant on some cameras
        """
        return 0

    def getGains(self, cameraport):
        """
        Return the list of gains for the camera port as strings
        """
        gains = list()
        return gains

    def getGain(self, cameraport):
        """
        Find the gain used
        """
        return 0

    def getGainName(self, cameraport, gain):
        """
        Get the label of the gain (low/Medium/High for instance
        """
        return "Unknown"

    def setGain(self, gain):
        """
        Select speed used on this port
        """
        return True

    def getReadoutTime(self):
        """
        Find the time added after exposure in order to read the device, if not blanked it is added to expsue time
        """
        return 0

    def getNumofPorts(self):
        """
        Find the number of cameras ports
        """
        return 0

    def getPortName(self, portnb):
        """
        Find the label of the camera port
        """
        return "Unknown"

    def getPortNames(self):
        """
        Find the label of the camera port
        """
        ports = ()
        return ports

    def getCurrentPort(self):
        """
        Returns the current port number
        """
        return 0

    def setCurrentPort(self, cameraport):
        """
        Choose the current port
        """
        return False

    def getMultiplication(self):
        """
        Returns the multiplication value minvalue and maxvalue of the EMCCD port
        """
        return 1, 0, 1024

    def setMultiplication(self, multiplication):
        """
        Set the multiplication value of the EMCCD port
        """
        pass

    def getCCDStatus(self) -> dict:
        """
        Returns the status of the acquisition
        now returns a dict
        """
        status = dict()
        return status

    def getReadoutSpeed(self):
        """
        Return expected frame rate
        """
        return 0

    def getPixelTime(self, cameraport, speed):
        """
        Returns time to shift a pixel for a specific port and speed
        """
        return 0

    def adjustOverscan(self, sizex, sizey):
        """
        Extend the size of the cdd chip - tested only on horizontal axis
        """
        pass

    def setTurboMode(self, active, sizex, sizey):
        """"
        Roper ProEM specific - fast and ultra high speed readout
        """
        pass

    def getTurboMode(self):
        """
        Roper ProEM specific - fast and ultra high speed readout
        """
        return False, 0, 0

    def setExposureMode(self, mode, edge):
        """"
        Defines exposure trigger (slave/master), and edge polarity if used
        """
        return False

    def getExposureMode(self):
        """
        Get exposure trigger (slave/master), and edge polarity if used
        """
        return False, 0

    def setPulseMode(self, mode):
        """
        Defines what pulses comes out from camera
        """
        return False

    def setVerticalShift(self, shift, clear):
        """
        Defines shift rate and number of cleans
        """
        return 0

    def setFan(self, On_Off: bool):
        """
        Turns the camera fan on or off
        """
        return False

    def getFan(self):
        """
        Read the camera fan state: on or off
        """
        return False

    def setArea(self, area: tuple):
        """
        Set the ROI read on the camera (tof, left, bottom, right)
        """
        return False

    def getArea(self):
        """
        Get the ROI read on the camera (tof, left, bottom, right)
        """
        return 0, 0, 256, 1024

    def setVideoThreshold(self, threshold):
        """
        Set the minimum level, if under value for the pixel is set to 0
        Set to zero to inhibit the function
        """
        pass

    def getVideoThreshold(self):
        """
        Get the minimum level, if under value for the pixel is set to 0
        """
        return 0

