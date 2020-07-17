"""
Class controlling orsay scan hardware.
"""
import sys
import threading
from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_short, c_long, c_bool, c_double, c_uint64, c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
from ctypes import c_ushort, c_ulong, c_float
from shutil import copy2

import os

__author__  = "Marcel Tence"
__status__  = "alpha"
__version__ = "0.1"

def _isPython3():
    return sys.version_info[0] >= 3

def _buildFunction(call, args, result):
    call.argtypes = args
    call.restype = result
    return call

def _createCharBuffer23(size):
    if (_isPython3()):
        return create_string_buffer(b'\000' * size)
    return create_string_buffer('\000' * size)

def _convertToString23(binaryString):
    if (_isPython3()):
        return binaryString.decode("utf-8")
    return binaryString

def _toString23(string):
    if (_isPython3()):
        return string.encode("utf-8")
    return string

# library must be in the same folder as this file.
if (sys.maxsize > 2**32):
    #first copy the extra dll to python folder
    libpath = os.path.dirname(__file__)
    python_folder = sys.executable
    pos = python_folder.find("python.exe")
    if pos>0:
        python_folder=python_folder.replace("python.exe","")
        lib2name=os.path.join(libpath, "STEMSerial.dll")
        copy2(lib2name,python_folder)
        lib3name = os.path.join(libpath, "Connection.dll")
        copy2(lib3name, python_folder)
        lib3nameconfig = os.path.join(libpath, "Connection.dll.config")
        copy2(lib3nameconfig, python_folder)
    libname = os.path.dirname(__file__)
    libname = os.path.join(libname, "Cameras.dll")
    _library = cdll.LoadLibrary(libname)
else:
    raise Exception("It must a python 64 bit version")

LOGGERFUNC = WINFUNCTYPE(None, c_char_p, c_bool)
DATALOCKFUNC = WINFUNCTYPE(c_void_p, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int))
DATAUNLOCKFUNC = WINFUNCTYPE(None, c_int, c_bool)
SPIMLOCKFUNC = WINFUNCTYPE(c_void_p, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int))
SPIMUNLOCKFUNC = WINFUNCTYPE(None, c_int, c_bool, c_bool)
SPECTLOCKFUNC = WINFUNCTYPE(c_void_p, c_int, POINTER(c_int), POINTER(c_int))
SPECTUNLOCKFUNC = WINFUNCTYPE(None, c_int, c_bool)
SPIMUPDATEFUNC = WINFUNCTYPE(None, c_int, c_bool)
CONNECTIONFUNC = WINFUNCTYPE(None, c_bool, c_bool)

class orsayCamera(object):
    """
    Class controlling orsay camera class
    Requires Cameras.dll library to run.
    """
    def __initialize_library(self):
        #	void CAMERAS_EXPORT *OrsayCamerasInit(int manufacturer, const char *model, void(*logger)(const char *buf, bool debug), bool simul);
        self.__OrsayCameraInit = _buildFunction(_library.OrsayCamerasInit, [c_int, c_char_p, c_char_p, LOGGERFUNC, c_bool],
                                           c_void_p)
        # void CAMERAS_EXPORT OrsayCamerasClose(void* o);
        self.__OrsayCameraClose = _buildFunction(_library.OrsayCamerasClose, [c_void_p], None)

        #	bool CAMERAS_EXPORT Simulation(void *o);
        self.__OrsayCameraSimulation = _buildFunction(_library.Simulation, [c_void_p], c_bool)

        # void CAMERAS_EXPORT RegisterLogger(void *o, void(*logger)(const char *, bool));
        self.__OrsayCameraRegisterLogger = _buildFunction(_library.RegisterLogger, [c_void_p, LOGGERFUNC], None)

        # void CAMERAS_EXPORT AddConnectionListener(void * o, void(*changed)(bool ismessage, bool on));
        self.__AddConnectionListener = _buildFunction(_library.AddConnectionListener, [c_void_p, CONNECTIONFUNC], None)

        # void CAMERAS_EXPORT RegisterDataLocker(void * o, void *(*LockDataPointer)(int cam,  int *datatype, int *sx, int *sy, int *sz));
        self.__OrsayCameraRegisterDataLocker = _buildFunction(_library.RegisterDataLocker, [c_void_p, DATALOCKFUNC], None)
        # void CAMERAS_EXPORT RegisterDataUnlocker(void *o, void(*UnLockDataPointer)(int cam, bool newdata));
        self.__OrsayCameraRegisterDataUnlocker = _buildFunction(_library.RegisterDataUnlocker, [c_void_p, DATAUNLOCKFUNC],
                                                           None)
        # void CAMERAS_EXPORT RegisterSpimDataLocker(void *o, void(*LockSpimDataPointer)(int cam, int *datatype, int *sx, int *sy, int *sz));
        self.__OrsayCameraRegisterSpimDataLocker = _buildFunction(_library.RegisterSpimDataLocker, [c_void_p, SPIMLOCKFUNC],
                                                             None)
        # void CAMERAS_EXPORT RegisterSpimDataUnlocker(void *o, void *(*UnLockSpimDataPointer)(int cam, bool newdata, bool running));
        self.__OrsayCameraRegisterSpimDataUnlocker = _buildFunction(_library.RegisterSpimDataUnlocker,
                                                               [c_void_p, SPIMUNLOCKFUNC], None)
        # //void ** (*LockOnlineSpimDataPointer)(void *o, short cam, short *datatype, short *sx, short *sy, short *sz);
        # //void(*UnLockOnlineSpimDataPointer)(void *o, int cam, bool newdata, bool running);
        # void CAMERAS_EXPORT RegisterSpectrumDataLocker(void *o, void *(*LockSpectrumDataPointer)(int cam, int *datatype, int *sx));
        self.__OrsayCameraRegisterSpectrumDataLocker = _buildFunction(_library.RegisterSpectrumDataLocker,
                                                                 [c_void_p, SPECTLOCKFUNC], None)
        # void CAMERAS_EXPORT RegisterSpectrumDataUnlocker(void *o, void(*UnLockSpectrumDataPointer)(int cam, bool newdata));
        self.__OrsayCameraRegisterSpectrumDataUnlocker = _buildFunction(_library.RegisterSpectrumDataUnlocker,
                                                                   [c_void_p, SPECTUNLOCKFUNC], None)
        # void CAMERAS_EXPORT RegisterSpimUpdateInfo(void *o, void(*UpdateSpimInfo)(unsigned long currentspectrum, bool running));
        self.__OrsayCameraRegisterSpimUpdateLocker = _buildFunction(_library.RegisterSpimUpdateInfo,
                                                               [c_void_p, SPIMUPDATEFUNC], None)

        # bool CAMERAS_EXPORT init_data_structures(void *o);
        self.__OrsayCameraInit_data_structures = _buildFunction(_library.init_data_structures, [c_void_p], c_bool)

        # void CAMERAS_EXPORT GetCCDSize(void *o, long *sx, long *sy);
        self.__OrsayCameraGetCCDSize = _buildFunction(_library.GetCCDSize, [c_void_p, POINTER(c_long), POINTER(c_long)],
                                                 None)
        # void CAMERAS_EXPORT GetImageSize(void *o, long *sx, long *sy);
        self.__OrsayCameraGetImageSize = _buildFunction(_library.GetImageSize, [c_void_p, ], None)

        # //myrgn_type GetArea(void *o, );
        # //bool CAMERAS_EXPORT SetCameraArea(void *o, short top, short left, short bottom, short right);
        self.__OrsayCameraSetArea = _buildFunction(_library.SetCameraArea, [c_void_p, c_short, c_short, c_short, c_short],
                                              c_bool)
        # bool CAMERAS_EXPORT GetCameraArea(void *o, short *top, short *left, short *bottom, short *right);#void CAMERAS_EXPORT SetCCDOverscan(void *o, int x, int y);
        self.__OrsayCameraGetArea = _buildFunction(_library.GetCameraArea,
                                              [c_void_p, POINTER(c_short), POINTER(c_short), POINTER(c_short),
                                               POINTER(c_short)], c_bool)
        # void CAMERAS_EXPORT SetCCDOverscan(void *o, int x, int y);
        self.__OrsayCameraSetCCDOverscan = _buildFunction(_library.SetCCDOverscan, [c_void_p, c_int, c_int], None)
        # void CAMERAS_EXPORT DisplayOverscan(void *o, bool on);
        self.__OrsayCameraDisplayOverscan = _buildFunction(_library.DisplayOverscan, [c_void_p, c_bool], None)
        # void CAMERAS_EXPORT GetBinning(void *o, unsigned short *bx, unsigned short *by);
        self.__OrsayCameraGetBinning = _buildFunction(_library.GetBinning, [c_void_p, POINTER(c_ushort), POINTER(c_ushort)],
                                                 None)
        # bool CAMERAS_EXPORT SetBinning(void *o, unsigned short bx, unsigned short by, bool estimatedark = true);
        self.__OrsayCameraSetBinning = _buildFunction(_library.SetBinning, [c_void_p, c_ushort, c_ushort, c_bool], c_bool)
        # void CAMERAS_EXPORT SetMirror(void *o, bool On);
        self.__OrsayCameraSetMirror = _buildFunction(_library.SetMirror, [c_void_p, c_bool], None)
        # void CAMERAS_EXPORT SetNbCumul(void *o, long n);
        self.__OrsayCameraSetNbCumul = _buildFunction(_library.SetNbCumul, [c_void_p, c_long], None)
        # long CAMERAS_EXPORT GetNbCumul(void *o);
        self.__OrsayCameraGetNbCumul = _buildFunction(_library.GetNbCumul, [c_void_p], c_long)
        # void CAMERAS_EXPORT SetSpimMode(void *o, unsigned short mode);
        self.__OrsayCameraSetSpimMode = _buildFunction(_library.SetSpimMode, [c_void_p, c_ushort], None)
        # bool CAMERAS_EXPORT StartSpim(void *o, unsigned long nbSpectra, unsigned long nbsp, float pose, bool saveK);
        self.__OrsayCameraStartSpim = _buildFunction(_library.StartSpim, [c_void_p, c_ulong, c_ulong, c_float, c_bool],
                                                c_bool)
        # bool CAMERAS_EXPORT ResumeSpim(void *o, int mode);
        self.__OrsayCameraResumeSpim = _buildFunction(_library.ResumeSpim, [c_void_p, c_int], c_bool)
        # bool CAMERAS_EXPORT PauseSpim(void *o);
        self.__OrsayCameraPauseSpim = _buildFunction(_library.PauseSpim, [c_void_p], c_bool)
        # bool CAMERAS_EXPORT StopSpim(void *o, bool endofline = false);
        self.__OrsayCameraStopSpim = _buildFunction(_library.StopSpim, [c_void_p, c_bool], c_bool)

        # void CAMERAS_EXPORT DisplayCCDInfos(void *o, char *filter);
        self.__OrsayCameraDisplayCCDInfos = _buildFunction(_library.DisplayCCDInfos, [c_void_p, c_char_p], None)
        # bool CAMERAS_EXPORT isCameraThere(void *o);
        self.__OrsayCameraIsCameraThere = _buildFunction(_library.isCameraThere, [c_void_p], c_bool)
        # bool CAMERAS_EXPORT GetTemperature(void *o, float *temperature, bool *status);
        self.__OrsayCameraGetTemperature = _buildFunction(_library.GetCameraTemperature,
                                                     [c_void_p, POINTER(c_float), POINTER(c_bool)], c_bool)
        # bool CAMERAS_EXPORT SetTemperature(void *o, float temperature);
        self.__OrsayCameraSetTemperature = _buildFunction(_library.SetCameraTemperature, [c_void_p, c_float], c_bool)
        # bool CAMERAS_EXPORT SetupBinning(void *o);
        self.__OrsayCameraSetupBinning = _buildFunction(_library.SetupBinning, [c_void_p], c_bool)
        # bool CAMERAS_EXPORT StartFocus(void *o, float pose, short display, short accumulate);
        self.__OrsayCameraStartFocus = _buildFunction(_library.StartFocus, [c_void_p, c_float, c_short, c_short], c_bool)
        # bool CAMERAS_EXPORT StopFocus(void *o);
        self.__OrsayCameraStopFocus = _buildFunction(_library.StopFocus, [c_void_p], c_bool)
        # bool CAMERAS_EXPORT SetCameraExposureTime(void *o, double pose);
        self.__OrsayCameraSetExposureTime = _buildFunction(_library.SetCameraExposureTime, [c_void_p, c_double], c_bool)
        # bool CAMERAS_EXPORT StartDarkCalibration(void *o, long numofimages);
        # self.__OrsayCameraStartDarkCalibration = _buildFunction(_library.StartDarkCalibration, [c_void_p, c_long], c_bool)
        # long CAMERAS_EXPORT GetNumOfSpeed(void *o, short p);
        self.__OrsayCameraGetNumOfSpeed = _buildFunction(_library.GetNumOfSpeed, [c_void_p, c_int], c_long)
        # long CAMERAS_EXPORT GetCurrentSpeed(void *o, short p);
        self.__OrsayCameraGetCurrentSpeed = _buildFunction(_library.GetCurrentSpeed, [c_void_p, c_short], c_long)
        # long CAMERAS_EXPORT SetSpeed(void *o, short p, long n);
        self.__OrsayCameraSetSpeed = _buildFunction(_library.SetSpeed, [c_void_p, c_short, c_long], c_long)
        # int CAMERAS_EXPORT GetNumOfGains(void *o, int p);
        self.__OrsayCameraGetNumOfGains = _buildFunction(_library.GetNumOfGains, [c_void_p, c_int], c_int)
        # const char CAMERAS_EXPORT *GetGainName(void *o, int p, int g);
        self.__OrsayCameraGetGainName = _buildFunction(_library.GetGainName, [c_void_p, c_int, c_int], c_char_p)
        # bool CAMERAS_EXPORT SetGain(void *o, short newgain);
        self.__OrsayCameraSetGain = _buildFunction(_library.SetCameraGain, [c_void_p, c_short], c_bool)
        # short CAMERAS_EXPORT GetGain(void *o);
        self.__OrsayCameraGetGain = _buildFunction(_library.GetGain, [c_void_p], c_short)
        # double CAMERAS_EXPORT GetReadOutTime(void *o);
        self.__OrsayCameraGetReadOutTime = _buildFunction(_library.GetCameraReadOutTime, [c_void_p], c_double)
        # long CAMERAS_EXPORT GetNumOfPorts(void *o);
        self.__OrsayCameraGetNumOfPorts = _buildFunction(_library.GetNumOfPorts, [c_void_p], c_long)
        # const char CAMERAS_EXPORT *GetPortName(void *o, long nb);
        self.__OrsayCameraGetPortName = _buildFunction(_library.GetPortName, [c_void_p, c_long], c_char_p)
        # long CAMERAS_EXPORT GetCurrentPort(void *o);
        self.__OrsayCameraGetCurrentPort = _buildFunction(_library.GetCurrentPort, [c_void_p], c_long)
        # bool CAMERAS_EXPORT SetCameraPort(void *o, long n);
        self.__OrsayCameraSetCameraPort = _buildFunction(_library.SetCameraPort, [c_void_p, c_long], c_bool)
        # unsigned short CAMERAS_EXPORT GetMultiplication(void *o, unsigned short *pmin, unsigned short *pmax);
        self.__OrsayCameraGetMultiplication = _buildFunction(_library.GetMultiplication,
                                                        [c_void_p, POINTER(c_ushort), POINTER(c_ushort)], c_ushort)
        # void CAMERAS_EXPORT SetMultiplication(void *o, unsigned short mult);
        self.__OrsayCameraSetMultiplication = _buildFunction(_library.SetMultiplication, [c_void_p, c_ushort], None)
        # void CAMERAS_EXPORT getCCDStatus(void *o, short *mode, double *p1, double *p2, double *p3, double *p4);
        self.__OrsayCameragetCCDStatus = _buildFunction(_library.getCCDStatus,
                                                   [c_void_p, POINTER(c_short), POINTER(c_double), POINTER(c_double),
                                                    POINTER(c_double), POINTER(c_double)], None)
        # double CAMERAS_EXPORT GetReadoutSpeed(void *o);
        self.__OrsayCameraGetReadoutSpeed = _buildFunction(_library.GetReadoutSpeed, [c_void_p], c_double)
        # long CAMERAS_EXPORT GetPixelTime(void *o, short p, short v);
        self.__OrsayCameraGetPixelTime = _buildFunction(_library.GetPixelTime, [c_void_p, c_short, c_short], c_long)
        # void CAMERAS_EXPORT AdjustOverscan(void *o, int sx, int sy);
        self.__OrsayCameraAdjustOverscan = _buildFunction(_library.AdjustOverscan, [c_void_p, c_int, c_int], None)
        # void CAMERAS_EXPORT SetTurboMode(void *o, int active, short horizontalsize, short verticalsize);
        self.__OrsayCameraSetTurboMode = _buildFunction(_library.SetTurboMode, [c_void_p, c_short, c_short, c_short], None)
        # int CAMERAS_EXPORT GetTurboMode(void *o, short *horizontalsize, short *verticalsize);
        self.__OrsayCameraGetTurboMode = _buildFunction(_library.GetTurboMode,
                                                   [c_void_p, POINTER(c_short), POINTER(c_short)], c_int)
        # bool CAMERAS_EXPORT SetExposureMode(void *o, short mode, short edge);
        self.__OrsayCameraSetExposureMode = _buildFunction(_library.SetExposureMode, [c_void_p, c_short, c_short], c_bool)
        # short CAMERAS_EXPORT GetExposureMode(void *o, short *edge);
        self.__OrsayCameraGetExposureMode = _buildFunction(_library.GetExposureMode, [c_void_p, POINTER(c_short)], c_short)
        # bool CAMERAS_EXPORT SetPulseMode(void *o, short mode);
        self.__OrsayCameraSetPulseMode = _buildFunction(_library.SetPulseMode, [c_void_p, c_int], c_bool)
        # bool CAMERAS_EXPORT SetVerticalShift(void *o, double shift, int clear);
        self.__OrsayCameraSetVerticalShift = _buildFunction(_library.SetVerticalShift, [c_void_p, c_double, c_int], c_bool)
        # bool CAMERAS_EXPORT SetFan(void *o, bool OnOff);
        self.__OrsayCameraSetFan = _buildFunction(_library.SetFan, [c_void_p, c_bool], c_bool)
        # bool CAMERAS_EXPORT GetFan(void *o);
        self.__OrsayCameraGetFan = _buildFunction(_library.GetFan, [c_void_p], c_bool)
        #	void CAMERAS_EXPORT SetVideoThreshold(void *o, unsigned short th);
        self.__OrsayCameraSetVideoThreshold = _buildFunction(_library.SetVideoThreshold, [c_void_p, c_ushort], None)
        #	unsigned short CAMERAS_EXPORT GetVideoThreshold(void *o);
        self.__OrsayCameraGetVideoThreshold = _buildFunction(_library.GetVideoThreshold, [c_void_p], c_ushort)

    def close(self):
        self.__OrsayCameraClose(self.orsaycamera)
        self.orsaycamera = None
    def __logger(self, message, debug):
        print(f"log: {_convertToString23(message)}")

    def __connection_listener(self, message, connected):
        print("listener")
        if message:
            self.messagesevent.set()
            if connected:
                print("Message connection Online")
            else:
                print("Message connection Offline")
        else:
            self.dataevent.set()
            if connected:
                print("Data connection Online")
            else:
                print("Data connection Offline")

    def __init__(self, manufacturer, model, sn, simul):
        self.__initialize_library()
        self.manufacturer = manufacturer
        self.fnlog = LOGGERFUNC(self.__logger)
        self.fnconnection = CONNECTIONFUNC(self.__connection_listener)
        self.messagesevent = threading.Event()
        self.dataevent = threading.Event()

        modelb = _toString23(model)
        self.orsaycamera = self.__OrsayCameraInit(manufacturer, modelb,  _toString23(sn), self.fnlog, simul)
        if not self.orsaycamera:
            raise Exception ("Camera not created")
        self.addConnectionListener(self.fnconnection)
        self.messagesevent.wait(5.0)
        self.messagesevent.clear()
        if not self.__OrsayCameraInit_data_structures(self.orsaycamera):
            raise Exception ("Camera not initialised properly")
        print(f"Camera: {self.__OrsayCameraIsCameraThere(self.orsaycamera)}")
        self.setAccumulationNumber(10)

    def registerLogger(self, fn):
        """
        Replaces the original logger function
        """
        self.__OrsayCameraRegisterLogger(self.orsaycamera, fn)

    def addConnectionListener(self, fn):
        self.__AddConnectionListener(self.orsaycamera, fn)

    @property
    def simulation_mode(self) -> bool:
        """
        Tell if camera is in simulation mode
        Usefull for spectrum imaging simulation
        """
        return self.__OrsayCameraSimulation(self.orsaycamera)

    def getImageSize(self) -> int:
        """
        Read size of image given by the current setting
        """
        sx = c_long()
        sy = c_long()
        self.__OrsayCameraGetImageSize(self.orsaycamera, byref(sx), byref(sy))
        return sx.value, sy.value

    def getCCDSize(self) -> (int, int):
        """
        Size of the camera ccd chip
        """
        sx = c_long()
        sy = c_long()
        self.__OrsayCameraGetCCDSize(self.orsaycamera, byref(sx), byref(sy))
        return (sx.value, sy.value)

    def registerDataLocker(self, fn):
        """"
        Function called to get data storage for a frame by frame readout
        """
        self.__OrsayCameraRegisterDataLocker(self.orsaycamera, fn)

    def registerDataUnlocker(self, fn):
        """
        Function called when data process is done for a frame by frame readout
        """
        self.__OrsayCameraRegisterDataUnlocker(self.orsaycamera, fn)

    def registerSpimDataLocker(self, fn):
       """
       Function called to get data storage for a spectrum image readout
       """
       self.__OrsayCameraRegisterSpimDataLocker(self.orsaycamera, fn)

    def registerSpimDataUnlocker(self, fn):
        """
        Function called when data process is done for a spectrum image readout
        """
        self.__OrsayCameraRegisterSpimDataUnlocker(self.orsaycamera, fn)

    def registerSpectrumDataLocker(self, fn):
       """
       Function called to get data storage for the current spectrum in spim readout
       """
       self.__OrsayCameraRegisterSpectrumDataLocker(self.orsaycamera, fn)

    def registerSpectrumDataUnlocker(self, fn):
        """
        Function called when data process is done he current spectrum in spim readout
        """
        self.__OrsayCameraRegisterSpectrumDataUnlocker(self.orsaycamera, fn)

    def setCCDOverscan(self, sx, sy):
        """
        For roper CCD cameras changes the size of the chip artificially to do online baseline correction (should 0,0 or 128,0)
        """
        self.__OrsayCameraSetCCDOverscan(self.orsaycamera, sx, sy)

    def displayOverscan(self, displayed):
        """
        When displayed set, the overscan area is displayed, changing image/spectrum size
        """
        self.__OrsayCameraDisplayOverscan(self.orsaycamera, displayed)

    def getBinning(self):
        """
        Return horizontal, vertical binning
        """
        bx = c_ushort(1)
        by = c_ushort(1)
        self.__OrsayCameraGetBinning(self.orsaycamera, byref(bx), byref(by))
        return bx.value, by.value

    def setBinning(self, bx, by):
        """
        Set  horizontal, vertical binning
        """
        self.__OrsayCameraSetBinning(self.orsaycamera, bx, by, 0)

    def setMirror(self, mirror):
        """
        If mirror true, horizontal data are flipped
        """
        self.__OrsayCameraSetMirror(self.orsaycamera, mirror)

    def setAccumulationNumber(self, count):
        """
        Define the number of images/spectra to sum (change to a property?
        """
        self.__OrsayCameraSetNbCumul(self.orsaycamera, count)

    def getAccumulateNumber(self):
        """
        Return the number of images/spectra to sum (change to a property?
        """
        return self.__OrsayCameraGetNbCumul(self.orsaycamera)

    def setSpimMode(self, mode):
        """
        Set the spim operating mode: 0:SPIMSTOPPED, 1:SPIMRUNNING, 2:SPIMPAUSED, 3:SPIMSTOPEOL, 4:SPIMSTOPEOF, 5:SPIMONLINE
        """
        self.__OrsayCameraSetSpimMode(self.orsaycamera, mode)

    def startSpim(self, nbspectra, nbspectraperpixel, dwelltime, is2D):
        """
        Start spectrum imaging acquisition
        """
        self.__OrsayCameraStartSpim(self.orsaycamera, nbspectra, nbspectraperpixel, dwelltime, c_bool(is2D))

    def pauseSpim(self):
        """
        Pause spectrum imaging acquisition no tested yet
        """
        self.__OrsayCameraPauseSpim(self.orsaycamera)

    def resumeSpim(self, mode):
        """
        Resume spectrum imaging acquisition with mode: 0:SPIMSTOPPED, 1:SPIMRUNNING, 2:SPIMPAUSED, 3:SPIMSTOPEOL, 4:SPIMSTOPEOF, 5:SPIMONLINE
        """
        self.__OrsayCameraResumeSpim(self.orsaycamera, mode)

    def stopSpim(self, immediate):
        return self.__OrsayCameraStopSpim(self.orsaycamera, immediate)

    def isCameraThere(self):
        """
        Check if the camera exists
        """
        return self.__OrsayCameraGetTemperature(self.orsaycamera)

    def getTemperature(self):
        """
        Read ccd temperature and locked status
        """
        temperature = c_float()
        status = c_bool()
        res = self.__OrsayCameraGetTemperature(self.orsaycamera, byref(temperature), byref(status))
        return temperature.value, status.value

    def setTemperature(self, temperature):
        """
        Set the ccd temperature target point
        """
        self.__OrsayCameraSetTemperature(self.orsaycamera, temperature)

    def setupBinning(self):
        """
        Adjust binning using all current parameters and load it to camera
        """
        self.__OrsayCameraSetupBinning(self.orsaycamera)

    def startFocus(self, exposure, displaymode, accumulate):
        """
        Start imaging displaymode: 1d, 2d  accumulate if images/spectra have to be summed
        """
        mode = 0
        if (displaymode == "1d"):
            mode = 1
        return self.__OrsayCameraStartFocus(self.orsaycamera, exposure, mode, accumulate)

    def stopFocus(self):
        """
        Stop imaging
        """
        return self.__OrsayCameraStopFocus(self.orsaycamera)

    def setExposureTime(self, exposure):
        """
        Defines exposure time, usefull to get then frame rate including readout time
        """
        return self.__OrsayCameraSetExposureTime(self.orsaycamera, exposure)

    def getNumofSpeeds(self, cameraport):
        """
        Find the number of speeds available for a specific readout port, they can be port dependant on some cameras
        """
        return  self.__OrsayCameraGetNumOfSpeed(self.orsaycamera, cameraport)

    def getSpeeds(self, cameraport):
        """
        Return the list of speeds for the cameraport as strings
        """
        nbspeeds = self.getNumofSpeeds(cameraport)
        speeds = list()
        for s in range(nbspeeds):
            pixeltime = self.getPixelTime(cameraport, s)
            speed = 1000 / pixeltime
            if speed < 1:
                speeds.append(str(1000000 / pixeltime) + " KHz")
            else:
                speeds.append(str(speed) + " MHz")
        return speeds

    def getCurrentSpeed(self, cameraport):
        """
        Find the speed used
        """
        if isinstance(cameraport, int):
            return self.__OrsayCameraGetCurrentSpeed(self.orsaycamera, c_short(cameraport))
        else:
            return 0

    def getAllPortsParams(self):
        """
        Find the list of speeds por all ports return a tuple of (port name, (speeds,), (gains,)
        """
        cp = self.getCurrentPort()
        nbports = self.getNumofPorts()
        allportsparams = ()
        for p in range(nbports):
            #self.setCurrentPort(p)
            portparams = (self.getPortName(p),)
            nbspeeds = self.getNumofSpeeds(p)
            speeds = ()
            #roperscientific gives pixel time in nanoseconds.
            for s in range(nbspeeds):
                #self.setSpeed(p, s)
                pixeltime = self.getPixelTime(p, s)
                speed = 1000 / pixeltime
                if speed < 1:
                    speed = str(1000000 /pixeltime) + " KHz"
                else:
                    speed = str(speed) + " MHz"
                speeds = speeds + (speed,)
            portparams = portparams + (speeds,)
            nbgains = self.getNumofGains(p)
            gains = ()
            for g in range(nbgains):
                gains = gains + ((self.getGainName(p, g), self.getGain(p)),)
            portparams = portparams + (gains,)
            allportsparams = allportsparams + (portparams,)
        return allportsparams

    def setSpeed(self, cameraport, speed):
        """
        Select speed used on this port
        """
        return self.__OrsayCameraSetSpeed(self.orsaycamera, cameraport, speed)

    def getNumofGains(self, cameraport):
        """
        Find the number of gains available for a specific readout port, they can be port dependant on some cameras
        """
        return  self.__OrsayCameraGetNumOfGains(self.orsaycamera, cameraport)

    def getGains(self, cameraport):
        """
        Return the list of gains for the cameraport as strings
        """
        nbgains = self.getNumofGains(cameraport)
        gains = list()
        for g in range(nbgains):
            gains.append(self.getGainName(cameraport, g))
        return gains

    def getGain(self, cameraport):
        """
        Find the speed used
        """
        return self.__OrsayCameraGetGain(self.orsaycamera, cameraport)

    def getGainName(self, cameraport, gain):
        """
        Get the label of the gain (low/Medium/High for instance
        """
        return _convertToString23(self.__OrsayCameraGetGainName(self.orsaycamera, cameraport, gain))

    def setGain(self, gain):
        """
        Select speed used on this port
        """
        #print(f"orsaycamera: setGain {gain}")
        res = self.__OrsayCameraSetGain(self.orsaycamera, gain)
        return res

    def getGain(self, cameraport):
        "Find the speed used"
        return self.__OrsayCameraGetGain(self.orsaycamera, cameraport)

    def getReadoutTime(self):
        """
        Find the time added after exposure in order to read the device, if not blanked it is added to expsue time
        """
        return self.__OrsayCameraGetReadOutTime(self.orsaycamera)

    def getNumofPorts(self):
        """
        Find the number of cameras ports
        """
        return self.__OrsayCameraGetNumOfPorts(self.orsaycamera)

    def getPortName(self, portnb):
        """
        Find the label of the camera port
        """
        return _convertToString23(self.__OrsayCameraGetPortName(self.orsaycamera, portnb))

    def getPortNames(self):
        """
        Find the label of the camera port
        """
        nbports = self.getNumofPorts()
        ports = ()
        k = 0
        while k < nbports:
            ports = ports + (_convertToString23(self.__OrsayCameraGetPortName(self.orsaycamera, k)),)
            k = k + 1
        return ports

    def getCurrentPort(self):
        """
        Returns the current port number
        """
        return self.__OrsayCameraGetCurrentPort(self.orsaycamera)

    def setCurrentPort(self, cameraport):
        """
        Choose the current port
        """
        if isinstance(cameraport, int):
            return self.__OrsayCameraSetCameraPort(self.orsaycamera, c_long(cameraport))
        else:
            print("cameraport not an integer")
            return False

    def getMultiplication(self):
        """
        Returns the multiplication value minvalue and maxvalue of the EMCCD port
        """
        minval = c_ushort()
        maxval = c_ushort()
        val = self.__OrsayCameraGetMultiplication(self.orsaycamera, byref(minval), byref(maxval))
        return val, minval.value, maxval.value

    def setMultiplication(self, multiplication):
        """
        Set the multiplication value of the EMCCD port
        """
        self.__OrsayCameraSetMultiplication(self.orsaycamera, multiplication)

    def getCCDStatus(self) -> dict():
        """
        Returns the status of the acquisition
        now returns a dict
        """
        mode = c_short()
        p1 = c_double()
        p2 = c_double()
        p3 = c_double()
        p4 = c_double()
        self.__OrsayCameragetCCDStatus(self.orsaycamera, byref(mode), byref(p1), byref(p2), byref(p3), byref(p4))
        mode = mode.value
        status = dict()
        if mode == -1:
            status["mode"] = "offline"
        elif mode == 0:
            status["mode"] = "idle"
            status["actual temp"] = p1.value
            status["target temp"] = p2.value
        elif mode == 3:
            status["mode"] = "focus"
            status["frames/seconds"] = p1.value,
        elif mode == 4:
            status["mode"] = "cumul"
            status["accumulation_count"] = p1.value
        elif mode == 6 or mode == 5:
            status["mode"] = "Spectrum imaging"
            status["current spectrum"] = p1.value
            status["total spectra"] = p2.value
        return status

    def getReadoutSpeed(self):
        """
        Return expected frame rate
        """
        return self.__OrsayCameraGetReadoutSpeed(self.orsaycamera)

    def getPixelTime(self, cameraport, speed):
        """
        Returns time to shift a pixel for a specific port and speed
        """
        return self.__OrsayCameraGetPixelTime(self.orsaycamera, cameraport, speed)

    def adjustOverscan(self, sizex, sizey):
        """
        Extend the size of the cdd chip - tested only on horizontal axis
        """
        self.__OrsayCameraAdjustOverscan(self.orsaycamera, sizex, sizey)

    def setTurboMode(self, active, sizex, sizey):
        """"
        Roper ProEM specific - fast and ultra high speed readout
        """
        self.__OrsayCameraSetTurboMode(self.orsaycamera, active, sizex, sizey)

    def getTurboMode(self):
        """
        Roper ProEM specific - fast and ultra high speed readout
        """
        sx = c_short()
        sy = c_short()
        res = self.__OrsayCameraGetTurboMode(self.orsaycamera, byref(sx), byref(sy))
        return res, sx.value, sy.value

    def setExposureMode(self, mode, edge):
        """"
        Defines exposure trigger (slave/master), and edge polarity if used
        """
        return self.__OrsayCameraSetExposureMode(self.orsaycamera, mode, edge).value

    def getExposureMode(self):
        """
        Get exposure trigger (slave/master), and edge polarity if used
        """
        trigger = c_short()
        res = self.__OrsayCameraGetExposureMode(self.orsaycamera, byref(trigger)).value
        return res, trigger.value

    def setPulseMode(self, mode):
        """
        Defines what pulses comes out from camera
        """
        return self.__OrsayCameraSetPulseMode(self.orsaycamera, mode).value

    def setVerticalShift(self, shift, clear):
        """
        Defines shift rate and number of cleans
        """
        return self.__OrsayCameraSetVerticalShift(self.orsaycamera, shift, clear).value

    def setFan(self, On_Off : bool):
        """
        Turns the camera fan on or off
        """
        return self.__OrsayCameraSetFan(self.orsaycamera, On_Off)

    def getFan(self):
        """
        Read the camera fan state: on or off
        """
        return self.__OrsayCameraGetFan(self.orsaycamera)

    def setArea(self, area : tuple):
        """
        Set the ROI read on the camera (tof, left, bottom, right)
        """
        return self.__OrsayCameraSetArea(self.orsaycamera, area[0], area[1], area[2], area[3])

    def getArea(self):
        """
        Get the ROI read on the camera (tof, left, bottom, right)
        """
        top = c_short()
        bottom = c_short()
        left = c_short()
        right = c_short()
        self.__OrsayCameraGetArea(self.orsaycamera, top, left, bottom, right)
        return top.value, left.value, bottom.value, right.value

    def setVideoThreshold(self, threshold):
        """
        Set the minimum level, if under value for the pixel is set to 0
        Set to zero to inhibit the function
        """
        self.__OrsayCameraSetVideoThreshold(self.orsaycamera, threshold)

    def getVideoThreshold(self):
        """
        Get the minimum level, if under value for the pixel is set to 0
        """
        return self.__OrsayCameraGetVideoThreshold(self.orsaycamera)

    def setCCDOverscan(self, sx, sy):
        self.__OrsayCameraSetCCDOverscan(self.orsaycamera, sx, sy)
        