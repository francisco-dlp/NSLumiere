"""
Class controlling orsay scan hardware.
"""
import sys
from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_short, c_long, c_bool, c_double, c_uint64, c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
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

#is64bit = sys.maxsize > 2**32
if (sys.maxsize > 2**32):
    libname = os.path.dirname(__file__)
    libname = os.path.join(libname, "Scan.dll")
    _library = cdll.LoadLibrary(libname)
    #print(f"OrsayScan library: {_library}")
else:
    raise Exception("It must a python 64 bit version")

# void *(*LockScanDataPointer)(int gene, int *datatype, int *sx, int *sy, int *sz);
LOCKERFUNC = WINFUNCTYPE(c_void_p, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int))
# void(*UnLockScanDataPointer)(int gene, bool newdata);
UNLOCKERFUNC = WINFUNCTYPE(None, c_int, c_bool)
UNLOCKERFUNCA = WINFUNCTYPE(None, c_int, c_int, c_int, POINTER(c_int))

EELS_SCAN_CLOCK = 2
CL_SCAN_CLOCK = 4

class orsayScan(object):
    """Class controlling orsay scan hardware
       Requires Scan.dll library to run.
    """
    def __initialize_library(self):
        """
        Make all direct dll function as protected.
        """
        # void SCAN_EXPORT *OrsayScanInit();
        self.__OrsayScanInit = _buildFunction(_library.OrsayScanInit, [c_bool], c_void_p)

        # void SCAN_EXPORT OrsayScanClose(void* o)
        self.__OrsayScanClose = _buildFunction(_library.OrsayScanClose, [c_void_p], None)

        # void SCAN_EXPORT OrsayScangetVersion(void* o, short *product, short *revision, short *serialnumber, short *major, short *minor);
        self.__OrsayScangetVersion = _buildFunction(_library.OrsayScangetVersion,
                                               [c_void_p, POINTER(c_short), POINTER(c_short), POINTER(c_short),
                                                POINTER(c_short), POINTER(c_short)], None)

        # int SCAN_EXPORT OrsayScanGetInputsCount(void* o);
        self.__OrsayScangetInputsCount = _buildFunction(_library.OrsayScanGetInputsCount, [c_void_p], c_int)

        # int SCAN_EXPORT OrsayScanGetInputProperties(void* o, int nb, bool &unipolar, double &offset, char *buffer);
        self.__OrsayScanGetInputProperties = _buildFunction(_library.OrsayScanGetInputProperties,
                                                       [c_void_p, c_int, POINTER(c_bool), POINTER(c_double), c_char_p],
                                                       c_int)

        #	bool SCAN_EXPORT OrsayScanSetInputProperties(void* o, int nb, bool unipolar, double offset);
        self.__OrsayScanSetInputProperties = _buildFunction(_library.OrsayScanSetInputProperties,
                                                       [c_void_p, c_int, c_bool, c_double], c_bool)

        # bool SCAN_EXPORT OrsayScansetImageSize(void *o, int gene, int x, int y);
        self.__OrsayScansetImageSize = _buildFunction(_library.OrsayScansetImageSize, [c_void_p, c_int, c_int, c_int],
                                                 c_bool)

        #	bool SCAN_EXPORT OrsayScangetImageSize(void *o, int gene, int *x, int *y);
        self.__OrsayScangetImageSize = _buildFunction(_library.OrsayScangetImageSize,
                                                 [c_void_p, c_int, POINTER(c_int), POINTER(c_int)], c_bool)

        # bool SCAN_EXPORT OrsayScansetImageArea(void* o, int gene, int sx, int sy, int xd, int xf, int yd, int yf);
        self.__OrsayScansetImageArea = _buildFunction(_library.OrsayScansetImageArea,
                                                 [c_void_p, c_int, c_int, c_int, c_int, c_int, c_int, c_int], c_bool)

        # bool SCAN_EXPORT OrsayScangetImageArea(void* o, int gene, int *sx, int *sy, int *xd, int *xf, int *yd, int *yf);
        self.__OrsayScangetImageArea = _buildFunction(_library.OrsayScangetImageArea,
                                                 [c_void_p, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int),
                                                  POINTER(c_int), POINTER(c_int), POINTER(c_int)], bool)

        # double SCAN_EXPORT OrsayScangetPose(void* o, int gene);
        self.__OrsayScangetPose = _buildFunction(_library.OrsayScangetPose, [c_void_p, c_int], c_double)

        # bool SCAN_EXPORT OrsayScansetPose(void* o, int gene, double time);
        self.__OrsayScansetPose = _buildFunction(_library.OrsayScansetPose, [c_void_p, c_int, c_double], c_bool)

        # double SCAN_EXPORT OrsayScanSetRetourLigne(void* o, int gene, double rt);
        self.__OrsayScanSetRetourLigne = _buildFunction(_library.OrsayScanSetRetourLigne, [c_void_p, c_int, c_double],
                                                        c_double)
        # double SCAN_EXPORT OrsayScanGetRetourligne(void* o, int gene);
        self.__OrsayScanGetRetourLigne = _buildFunction(_library.OrsayScanGetRetourLigne, [c_void_p, c_int], c_double)

        # double SCAN_EXPORT OrsayScanGetImageTime(void* o, int gene);
        self.__OrsayScanGetImageTime = _buildFunction(_library.OrsayScanGetImageTime, [c_void_p, c_int], c_double)

        # bool SCAN_EXPORT OrsayScanSetInputs(void* o, int gene, int nb, int *inputs);
        self.__OrsayScanSetInputs = _buildFunction(_library.OrsayScanSetInputs, [c_void_p, c_int, c_int, POINTER(c_int)],
                                              c_bool)

        # int SCAN_EXPORT OrsayScanGetInputs(void* o, int gene, int *inputs);
        self.__OrsayScanGetInputs = _buildFunction(_library.OrsayScanGetInputs, [c_void_p, c_int, POINTER(c_int)], c_int)

        # void SCAN_EXPORT OrsayScanSetRotation(void* o, double angle);
        self.__OrsayScanSetRotation = _buildFunction(_library.OrsayScanSetRotation, [c_void_p, c_double], None)

        # double SCAN_EXPORT OrsayScanGetRotation(void* o);
        self.__OrsayScanGetRotation = _buildFunction(_library.OrsayScanGetRotation, [c_void_p], c_double)

        # bool SCAN_EXPORT OrsayScanStartImaging(void* o, short gene, short mode, short lineaverage);
        self.__OrsayScanStartImaging = _buildFunction(_library.OrsayScanStartImaging, [c_void_p, c_short, c_short, c_short],
                                                 c_bool)

        # bool SCAN_EXPORT OrsayScanStartSpim(void* o, short gene, short mode, short lineaverage, int nbspectraperpixel, bool sumpectra);
        self.__OrsayScanStartSpim = _buildFunction(_library.OrsayScanStartSpim,
                                              [c_void_p, c_short, c_short, c_short, c_int, c_bool], c_bool)

        # bool SCAN_EXPORT OrsayScanStopImaging(void* o, int gene, bool cancel);
        self.__OrsayScanStopImaging = _buildFunction(_library.OrsayScanStopImaging, [c_void_p, c_int, c_bool], c_bool)

        # bool SCAN_EXPORT OrsayScanStopImagingA(void* o, int gene, bool immediate);
        self.__OrsayScanStopImagingA = _buildFunction(_library.OrsayScanStopImagingA, [c_void_p, c_int, c_bool], c_bool)

        # void SCAN_EXPORT OrsayScanSetImagingMode(void* o, int gene, int stripes);
        self.__OrsayScanSetImagingMode = _buildFunction(_library.OrsayScanSetImagingMode, [c_void_p, c_int, c_int], None);

        # bool SCAN_EXPORT OrsayScanSetScanClock(void* o, int gene, int mode);
        self.__OrsayScanSetScanClock = _buildFunction(_library.OrsayScanSetScanClock, [c_void_p, c_int, c_int], c_bool)

        # unsigned long SCAN_EXPORT OrsayScanGetScansCount(void* o);
        self.__OrsayScanGetScansCount = _buildFunction(_library.OrsayScanGetScansCount, [c_void_p], c_uint32)

        # void SCAN_EXPORT OrsayScanSetScale(void* o, int sortie, double vx, double vy);
        self.__OrsayScanSetScale = _buildFunction(_library.OrsayScanSetScale, [c_void_p, c_int, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanSetImagingKind(void *o, int gene, int kind);
        self.__OrsayScanSetImagingKind = _buildFunction(_library.OrsayScanSetImagingKind, [c_void_p, c_int, c_int], None)

        # int SCAN_EXPORT OrsayScanGetImagingKind(void *o, int gene);
        self.__OrsayScanGetImagingKind = _buildFunction(_library.OrsayScanGetImagingKind, [c_void_p, c_int], c_int)

        # double SCAN_EXPORT OrsayScanGetVideoOffset(void *o, int index);
        self.__OrsayScanGetVideoOffset = _buildFunction(_library.OrsayScanGetVideoOffset, [c_void_p, c_int], c_double)

        # void SCAN_EXPORT OrsayScanSetVideoOffset(void *o, int index, double value);
        self.__OrsayScanSetVideoOffset = _buildFunction(_library.OrsayScanSetVideoOffset, [c_void_p, c_int, c_double], None)
        # bool SCAN_EXPORT OrsayScanSetFieldSize(self.orsayscan, double field);
        self.__OrsayScanSetFieldSize = _buildFunction(_library.OrsayScanSetFieldSize, [c_void_p, c_double], c_bool)

        # void SCAN_EXPORT OrsayScanRegisterDataLocker(void * o, void *(*LockScanDataPointer)(int gene, int *datatype, int *sx, int *sy, int *sz));
        self.__OrsayScanregisterLocker = _buildFunction(_library.OrsayScanRegisterDataLocker, [c_void_p, LOCKERFUNC], None)
        # void SCAN_EXPORT OrsayScanRegisterDataUnlocker(void *o, void(*UnLockScanDataPointer)(int gene, bool newdata));
        self.__OrsayScanregisterUnlocker = _buildFunction(_library.OrsayScanRegisterDataUnlocker, [c_void_p, UNLOCKERFUNC],
                                                     None)
        self.__OrsayScanregisterUnlockerA = _buildFunction(_library.OrsayScanRegisterDataUnlockerA,
                                                      [c_void_p, UNLOCKERFUNCA], None)

        # bool SCAN_EXPORT OrsayScanSetProbeAt(self.orsayscan, int gene, int px, int py);
        self.__OrsayScanSetProbeAt = _buildFunction(_library.OrsayScanSetProbeAt, [c_void_p, c_int, c_int, c_int], c_bool)

        # void SCAN_EXPORT OrsayScanSetEHT(self.orsayscan, double val);
        self.__OrsayScanSetEHT = _buildFunction(_library.OrsayScanSetEHT, [c_void_p, c_double], None)

        # double SCAN_EXPORT OrsayScanGetEHT(self.orsayscan);
        self.__OrsayScanGetEHT = _buildFunction(_library.OrsayScanGetEHT, [c_void_p], c_double)

        # double SCAN_EXPORT OrsayScanGetMaxFieldSize(self.orsayscan);
        self.__OrsayScanGetMaxFieldSize = _buildFunction(_library.OrsayScanGetMaxFieldSize, [c_void_p], c_double)

        # double SCAN_EXPORT OrsayScanGetFieldSize(self.orsayscan);
        self.__OrsayScanGetFieldSize = _buildFunction(_library.OrsayScanGetFieldSize, [c_void_p], c_double)

        # double SCAN_EXPORT OrsayScanGetScanAngle(self.orsayscan, short *mirror);
        self.__OrsayScanGetScanAngle = _buildFunction(_library.OrsayScanGetScanAngle, [c_void_p, c_short], c_double)

        # bool SCAN_EXPORT OrsayScanSetFieldSize(self.orsayscan, double field);
        self.__OrsayScanSetFieldSize = _buildFunction(_library.OrsayScanSetFieldSize, [c_void_p, c_double], c_bool)

        # bool SCAN_EXPORT OrsayScanSetBottomBlanking(self.orsayscan, short mode, short source, double beamontime, bool risingedge, unsigned int nbpulses, double delay);
        self.__OrsayScanSetBottomBlanking = _buildFunction(_library.OrsayScanSetBottomBlanking,
                                                      [c_void_p, c_short, c_short, c_double, c_bool, c_uint, c_double], c_bool)

        # bool SCAN_EXPORT OrsayScanSetTopBlanking(self.orsayscan, short mode, short source, double beamontime, bool risingedge, unsigned int nbpulses, double delay);
        self.__OrsayScanSetTopBlanking = _buildFunction(_library.OrsayScanSetTopBlanking,
                                                   [c_void_p, c_short, c_short, c_double, c_bool, c_uint, c_double], c_bool)

        #	bool SCAN_EXPORT OrsayScanSetTdcLine(void *o, short index, short mode, short source, double period, double ontime, bool risingedge, unsigned int nbpulses, double delay);
        self.__OrsayScanSetTdcLine = _buildFunction(_library.OrsayScanSetTdcLine,
                                                    [c_void_p, c_short, c_short, c_short, c_double, c_double, c_bool, c_uint32, c_double], c_bool)

        # bool SCAN_EXPORT OrsayScanSetCameraSync(self.orsayscan, bool eels, int divider, double width, bool risingedge);
        self.__OrsayScanSetCameraSync = _buildFunction(_library.OrsayScanSetCameraSync,
                                                  [c_void_p, c_bool, c_int, c_double, c_bool], c_bool)

        # void SCAN_EXPORT OrsayScanObjectiveStigmateur(self.orsayscan, double x, double y);
        self.__OrsayScanObjectiveStigmateur = _buildFunction(_library.OrsayScanObjectiveStigmateur,
                                                        [c_void_p, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanObjectiveStigmateurCentre(self.orsayscan, double xcx, double xcy, double ycx, double ycy);
        self.__OrsayScanObjectiveStigmateurCentre = _buildFunction(_library.OrsayScanObjectiveStigmateurCentre,
                                                              [c_void_p, c_double, c_double, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanCondensorStigmateur(self.orsayscan, double x, double y);
        self.__OrsayScanCondensorStigmateur = _buildFunction(_library.OrsayScanCondensorStigmateur,
                                                        [c_void_p, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanGrigson(self.orsayscan, double x1, double x2, double y1, double y2);
        self.__OrsayScanGrigson = _buildFunction(_library.OrsayScanGrigson,
                                            [c_void_p, c_double, c_double, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanAlObjective(self.orsayscan, double x1, double x2, double y1, double y2);
        self.__OrsayScanAlObjective = _buildFunction(_library.OrsayScanAlObjective,
                                                [c_void_p, c_double, c_double, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanAlGun(self.orsayscan, double x1, double x2, double y1, double y2);
        self.__OrsayScanAlGun = _buildFunction(_library.OrsayScanAlGun, [c_void_p, c_double, c_double, c_double, c_double],
                                          None)

        # void SCAN_EXPORT OrsayScanAlStigObjective(self.orsayscan, double x1, double x2, double y1, double y2);
        self.__OrsayScanAlStigObjective = _buildFunction(_library.OrsayScanAlStigObjective,
                                                    [c_void_p, c_double, c_double, c_double, c_double], None)

        # void SCAN_EXPORT OrsayScanSetLaser(self.orsayscan, double frequency, int nbpulses, bool bottomblanking, short sync);
        self.__OrsayScanSetLaser = _buildFunction(_library.OrsayScanSetLaser, [c_void_p, c_double, c_int, c_bool, c_short],
                                             None)

        # void SCAN_EXPORT OrsayScanStartLaser(self.orsayscan, int mode);
        self.__OrsayScanStartLaser = _buildFunction(_library.OrsayScanStartLaser, [c_void_p, c_int], None)

        # void SCAN_EXPORT OrsayScanStartLaserA(self.orsayscan, int mode, short source);
        self.__OrsayScanStartLaserA = _buildFunction(_library.OrsayScanStartLaserA, [c_void_p, c_int, c_short], None)

        # void SCAN_EXPORT OrsayScanCancelLaser(self.orsayscan);
        self.__OrsayScanCancelLaser = _buildFunction(_library.OrsayScanCancelLaser, [c_void_p], None)

        # int SCAN_EXPORT OrsayScanGetLaserCount(self.orsayscan);
        self.__OrsayScanGetLaserCount = _buildFunction(_library.OrsayScanGetLaserCount, [c_void_p], c_int)

        #	double SCAN_EXPORT GetClockSimulationTime(void *o, int gene);
        self.__OrsayScanGetClockSimulationTime = _buildFunction(_library.GetClockSimulationTime, [c_void_p, c_int], c_double)
        #	void SCAN_EXPORT SetClockSimulationTime(void *o, int gene, double dt);
        self.__OrsayScanSetClockSimulationTime = _buildFunction(_library.SetClockSimulationTime, [c_void_p, c_int, c_double],
                                                           None)

        # double SCAN_EXPORT OrsayScanGetPMT(self.orsayscan, int index);
        self.__OrsayScanGetPMT = _buildFunction(_library.OrsayScanGetPMT, [c_void_p, c_int], c_double)

        # void SCAN_EXPORT OrsayScanSetPMT(self.orsayscan, int index, double value);
        self.__OrsayScanSetPMT = _buildFunction(_library.OrsayScanSetPMT, [c_void_p, c_int, c_double], None)

        # int SCAN_EXPORT OrsayScanCountPMTs (self.orsayscan)
        self.__OrsayScanCountPMTs = _buildFunction(_library.OrsayScanCountPMTs, [c_void_p], c_int)

        # bool SCAN_EXPORT OrsayScanGetPMTLimits(self.orsayscan, int index, double &vmin, double & vmax)
        self.__OrsayScanGetPMTLimits=_buildFunction(_library.OrsayScanGetPMTLimits, [c_void_p, c_int, c_double, c_double], c_bool)




    def __init__(self, gene, scandllobject = 0, vg=False):
        self.__initialize_library()
        self.gene = gene
        cproduct = c_short()
        crevision = c_short()
        cserialnumber = c_short()
        cmajor = c_short()
        cminor = c_short()
        if (gene < 2):
            self.orsayscan = self.__OrsayScanInit(not vg)
        if (gene > 1):
            self.orsayscan = scandllobject
        self.__OrsayScangetVersion(self.orsayscan, byref(cproduct), byref(crevision), byref(cserialnumber), byref(cmajor), byref(cminor))
        self._product = cproduct.value
        self._revision = crevision.value
        self._serialnumber = cserialnumber.value
        self._major = cmajor.value
        self._minor = cminor.value
        if self._major < 5:
            raise AttributeError("No device connected")

    def close(self):
        self.__OrsayScanClose(self.orsayscan)
        self.orsaycamera = None

    def __verifyUnsigned32Bit(self, value):
        """
        Check if value is in range 0 <= value <= 0xffffffff
        """
        if(value < 0 or value > 0xffffffff):
            raise AttributeError("Argument out of range (must be 32bit unsigned).")

    def __verifySigned32Bit(self, value):
        """
        Check if value is in range 0 <= value <= 0xffffffff
        """
        if(value < 0x8000000 or value > 0x7fffffff):
            raise AttributeError("Argument out of range (must be 32bit signed).")

    def __verifyPositiveInt(self, value):
        """
        Check if value is in range 0 <= value <= 0xffffffff
        """
        if(value < 0 or value > 0x7fffffff):
            raise AttributeError("Argument out of range (must be positive 32bit signed).")

    def __verifyStrictlyPositiveInt(self, value):
        """
        Check if value is in range 0 < value <= 0xffffffff
        """
        if(value < 0 or value > 0x7fffffff):
            raise AttributeError("Argument out of range (must be positive 32bit signed).")

    def getInputsCount(self) -> int:
        """
        Donne le nombre d'entrées vidéo actives
        """
        return self.__OrsayScangetInputsCount(self.orsayscan)

    def getInputProperties(self, input : int) -> (int, float, str, int):
        """
        Lit les propriétés de l'entrée vidéo
        Retourne 3 valeurs: bool vrai si unipolaire, double offset, string nom, index de l'entrée.
        """
        unipolar = c_bool()
        offset = c_double()
        buffer = _createCharBuffer23(100)
        res = self.__OrsayScanGetInputProperties(self.orsayscan, input, byref(unipolar), byref(offset), buffer)
        return unipolar.value, offset.value, _convertToString23(buffer.value), input

    def setInputProperties(self, input : int, unipolar : bool, offset : float) -> bool:
        """
        change les propriétés de l'entrée vidéo
        Pour le moment, seul l'offset est utilisé.
        """
        res =self.__OrsayScanSetInputProperties(self.orsayscan, input, offset)
        if (not res):
            raise Exception("Failed to set orsayscan input properties")
        return res

    def GetImageTime(self) -> float:
        """
        Donne le temps effectif de la durée de balayage d'une image
        """
        return self.__OrsayScanGetImageTime(self.orsayscan, self.gene)

    def SetInputs(self, inputs : []) -> bool:
        """
        Choisit les entrées à lire.
        A cause d'une restriction hardware, les valeurs possibles sont 1, 2, 4, 6, 8
        """
        inputarray = (c_int * len(inputs))()
        k = 0
        while (k < len(inputs)):
            inputarray[k] = inputs[k]
            k = k +1
        return self.__OrsayScanSetInputs(self.orsayscan, self.gene, len(inputarray), inputarray)

    def GetInputs(self) ->(int, []):
        """
        Donne la liste des entrées utilisées
        """
        inputarray = (c_int * 20)()
        nbinputs = self.__OrsayScanGetInputs(self.orsayscan, self.gene, inputarray)
        inputs = []
        for inp in range(0, nbinputs):
            inputs.append(inputarray[inp])
        return nbinputs, inputs

    def setImageSize(self, sizex : int, sizey : int) -> bool:
        """
        Définit la taille de l'image en pixels
        Les limites de dimension sont 1 et 8192
        """
        self.__verifyPositiveInt(sizex)
        self.__verifyPositiveInt(sizey)
        res = self.__OrsayScansetImageSize(self.orsayscan, self.gene, sizex, sizey)
        if (not res):
            raise Exception("Failed to set orsayscan image size")

    def getImageSize(self) -> (int, int):
        """
        Donne la taille de l'image
        *** il est impératif que le tableau passé à la callback ait cette taille
            multiplié par le nombre d'entrées, multiplié par le paramètre lineaveragng ***
        """
        sx = c_int()
        sy = c_int()
        res = self.__OrsayScangetImageSize(self.orsayscan, self.gene, byref(sx), byref(sy))
        if (not res):
            raise Exception("Failed to get orsayscan image size")
        return int(sx.value), int(sy.value)

    def setImageArea(self, sizex : int, sizey : int, startx : int, endx : int, starty : int, endy : int) -> bool:
        """
        Définit une aire pour le balayage.
        Définit une aire pour le balayage.
        sizex, sizey taille de l'image complète
        startx, endx début et fin de la largeur du rectangle
        starty, endy début et fin de la hauteur.
        """
#        self.__verifyStrictlyPositiveInt(sizex)
#        self.__verifyStrictlyPositiveInt(sizey)
        return self.__OrsayScansetImageArea(self.orsayscan, self.gene, sizex, sizey, startx, endx, starty, endy)

    def getImageArea(self) -> (bool, int, int, int, int, int, int):
        """
        Donne l'aire réduite utilisée,
        retourne les paramètres donnés à la fonction setImageArea ou ceux les plus proches valides.
        """
        sx, sy, stx, ex, sty, ey = c_int(), c_int(), c_int(), c_int(), c_int(), c_int()
        res = self.__OrsayScangetImageArea(self.orsayscan, self.gene, byref(sx), byref(sy), byref(stx), byref(ex), byref(sty), byref(ey))
        return res, int(sx.value), int(sy.value), int(stx.value), int(ex.value), int(sty.value), int(ey.value)

    @property
    def pixelTime(self) -> float:
        """
        Donne le temps par pixel
        """
        return self.__OrsayScangetPose(self.orsayscan, self.gene)

    @pixelTime.setter
    def pixelTime(self, value : float):
        """
        Définit le temps par pixel
        """
        self.__OrsayScansetPose(self.orsayscan, self.gene, value)

    #
    #   Callback qui sera appelée lors d'arrivée de nouvelles données
    #
    def registerLocker(self, fn):
        """
        Définit la fonction callback appelée lorsque de nouvelles données sont présentes
        Elle a pour but de passer un tableau image sa dimension et son type de données
        On ne doit détruire cet objet avant l'appel d'une fonction unlock
        Voir programme demo.
        """
        self.__OrsayScanregisterLocker(self.orsayscan, fn)

    def registerUnlocker(self, fn):
        """
        Definit la fonction appelée à la fin du transfert de données.
        recoit newdata vrai si de nouvelles données sont effectivement là.
        Utiliser de préférence la fonction registerUnlockerA plus riche en informations sur le flux de données
        voir programe demo
        """
        self.__OrsayScanregisterUnlocker(self.orsayscan, fn)

    def registerUnlockerA(self, fn):
        """
        Definit la fonction appelée à la fin du transfert de données.
        reçoit newdata, le numéro de séquence de l'image en cours, rect: les coordonnées du rect où les données ont été modifiées.
        voir programe demo
        """
        self.__OrsayScanregisterUnlockerA(self.orsayscan, fn)

    def startSpim(self, mode : int, linesaveraging : int, Nspectra=1, save2D=False) -> bool:
        """
        Démarre l'acquitisition de l'image.
        mode: --- expliqué plus tard ---
        lineaveraging: nombre de lignes à faire avant de passer à la ligne suivante.
        retourne vrai si l'acquisition a eu lieu.
        """
        return self.__OrsayScanStartSpim(self.orsayscan, self.gene, mode, linesaveraging,Nspectra,save2D)

    def setScanClock(self,trigger_input=0) -> bool:
        """
        set the input line for starting the next pixel in the STEM imaging (pin 9 and 5 on subD9)
        Parameters
        ----------
        trigger_input: 0 for pin 9, 1 for pin 5, 2 for CL ready, 3 for In3, 4 for EELS ready

        Returns
        -------

        """
        return self.__OrsayScanSetScanClock(self.orsayscan, self.gene, trigger_input)

    def startImaging(self, mode : int, linesaveraging : int) -> bool:
        """
        Démarre l'acquitisition de l'image.
        mode: --- expliqué plus tard ---
        lineaveraging: nombre de lignes à faire avant de passer à la ligne suivante.
        retourne vrai si l'acquisition a eu lieu.
        """
        return self.__OrsayScanStartImaging(self.orsayscan, self.gene, mode, linesaveraging)

    def stopImaging(self, cancel : bool) -> bool:
        """
        Arrete l'acquisition d'images
        cancel vrai => immédiat,  faux => à la fin du scan de l'image en cours
        """
        return self.__OrsayScanStopImaging(self.orsayscan, self.gene, cancel)

    def getScanCount(self) -> int:
        """
        Donne le nombe de balayages déjà faits
        """
        return self.__OrsayScanGetScansCount(self.orsayscan)

    def setScanRotation(self, angle : float):
        """
        Définit l'angle de rotation du balayage de l'image
        """
        self.__OrsayScanSetRotation(self.orsayscan, angle)

    def getScanRotation(self) -> float:
        """
        Relit la valeur de l'angle de rotation du balayage de l'image
        """
        return self.__OrsayScanGetRotation(self.orsayscan)

    def setScanScale(self, plug, xamp : float, yamp : float):
        """
        Ajuste la taille des signaux analogiques de balayage valeur >0 et inf"rieure à 1.
        """
        self.__OrsayScanSetScale(self.orsayscan, plug, xamp, yamp)

    def getImagingKind(self) -> int:
        kind = self.__OrsayScanGetImagingKind(self.orsayscan, self.gene)
        return kind

    def setVideoOffset(self, inp : int, offset : float):
        """
        Définit l'offset analogique à ajouter au signal d'entrée afin d'avoir une valeur 0 pour 0 volts
        En principe, c'est un réglage et pour une machine cela ne devrait pas bouger beaucoup
        """
        self.__OrsayScanSetVideoOffset(self.orsayscan, inp, offset)

    def getVideoOffset(self, inp : int) -> float:
        """
        Donne la valeur de l'offset vidéo
        """
        return self.__OrsayScanGetVideoOffset(self.orsayscan, inp)

    def SetProbeAt(self, px : int, py : int):
    # bool SCAN_EXPORT OrsayScanSetProbeAt(self.orsayscan, int gene, int px, int py);
       return self.__OrsayScanSetProbeAt(self.orsayscan, self.gene, px, py)

   #void SCAN_EXPORT OrsayScanSetEHT(self.orsayscan, double val);
    def SetEHT(self, val):
        self.__OrsayScanSetEHT(self.orsayscan,val)

    def GetEHT(self):
        return self.__OrsayScanGetEHT(self.orsayscan)

   #double SCAN_EXPORT OrsayScanGetMaxFieldSize(self.orsayscan);
    def GetMaxFieldSize(self):
        return self.__OrsayScanGetMaxFieldSize(self.orsayscan)

   #double SCAN_EXPORT OrsayScanGetFieldSize(self.orsayscan);
    def GetFieldSize(self):
        return self.__OrsayScanGetFieldSize(self.orsayscan)

   #double SCAN_EXPORT OrsayScanGetScanAngle(self.orsayscan, short *mirror);
    def GetScanAngle(self,mirror):
        return self.__OrsayScanGetScanAngle(self.orsayscan, mirror)
   #bool SCAN_EXPORT OrsayScanSetFieldSize(self.orsayscan, double field);
    def SetFieldSize(self,field):
        return self.__OrsayScanSetFieldSize(self.orsayscan,  field)

   #bool SCAN_EXPORT OrsayScanSetBottomBlanking(self.orsayscan, short mode, short source, double beamontime, bool risingedge, unsigned int nbpulses, double delay);
    def SetBottomBlanking(self,mode,source,beamontime=0,risingedge=True,nbpulses=0,delay=0):
        """ Définit le blanker avant l'échantillon sur un VG/Nion
            mode : 0 blanker off, 1 blanker On, 2 controlled by source,
            3 controlled by source but with locally defined time (beamontime parametre)
            source : to be choosen based on configuration file (eels
            camera readout, cl camera readout, laser pulse, ...)
            beamontime : with of the Blanker on signal, for instance CCD
            vertical transfer time, laser pulse width, ...
            risingedge : choose the edge that triggers the beamontime.
            nbpulses : number of pulses required a signal is generated
            (used to sync slave cameras)
            delay : delay used to generate the beamon signal after the
            trigger. if nbpulses != 0, this delay is incremented nbpulses times.
            (very specific application not tested yet).
        """
        return self.__OrsayScanSetBottomBlanking(self.orsayscan,mode, source,beamontime,risingedge,nbpulses,delay)
   #bool SCAN_EXPORT OrsayScanSetTopBlanking(self.orsayscan, short mode, short source, double beamontime, bool risingedge, unsigned int nbpulses, double delay);
    def SetTopBlanking(self,mode, source,beamontime = 0, risingedge = True, nbpulses = 0, delay = 0):
        """ Définit le blanker après l'échantillon sur un VG/Nion
            mode : 0 blanker off, 1 blanker On, 2 controlled by source, 3 controlled by source but with locally defined time (beamontime parametre)
            source : to be choosen based on configuration file (eels camera readout, cl camera readout, laser pulse, ...)
            beamontime : with of the Blanker on signal, for instance CCD vertical transfer time, laser pulse width, ...
            risingedge : choose the edge that triggers the beamontime.
            nbpulses : number of pulses required a signal is generated (used to sync slave cameras)
            delay : delay used to generate the beamon signal after the trigger. if nbpulses != 0, this delay is incremented nbpulses times.
            (very specific application not tested yet).
        """
        return self.__OrsayScanSetTopBlanking(self.orsayscan,mode, source,beamontime,risingedge,nbpulses,delay)

    #	bool SCAN_EXPORT OrsayScanSetTdcLine(void *o, short index, short mode, short source, double period, double ontime, bool risingedge, unsigned int nbpulses, double delay);
    def SetTdcLine(self, line, mode, source, period=0.004, on_time=0.000005, rising_edge=True, nb_pulses=0, delay=0):
        """defines how "Tdc" (CheeTah) works. Output Tdc are defined in scan.xml. If not does nothing.
            line : 0 ou 1
            mode : 0 => 0
                 : 1 => 1
                 : 2 copy of source
                 : 3 copy of source, fix output with (on_time, larger or smaller) if delay > 0 output is delayed
                 : 4
                 : 5
                 : 6
                 : 7 internal generator nbpulses = 0 continuous, nbpulses > 0 limited number of pulses
            source : from 0 to 5 input IO of the box
                   : 5 scan generator 1 pixel clock (imaging mode)
                   : 6 scan generator 2 pixel clock (spectrum imaging mode)
                   : 7 blanking, falling edge means start of the line
                   : from 8 to 15 output line of the box. Should be different of Tdc Line of course, laser line is nice.
            period : frequency of internal generator (20 ns step)
            ontime : ontime (2.5 ns step)
            risingedge : edge used for mode > 2
            delay : when > 0 output is delayed
        """
        return self.__OrsayScanSetTdcLine(self.orsayscan, line, mode, source, period, on_time, rising_edge, nb_pulses, delay)

   #bool SCAN_EXPORT OrsayScanSetCameraSync(self.orsayscan, bool eels, int divider, double width, bool risingedge);
    def SetCameraSync(self,eels,divider,width,risingedge):
        """ Définit le mode de travail de la camera, par défaut la camera eels est maître
            eels: True => master, False => Slave
            divider: si mode slave, nombre d'impulsions pour avoir un trigger
            width: Largeur de l'impulsion
            risingedge: front utiliser pour compter l'impulsion.
        """
        return self.__OrsayScanSetCameraSync(self.orsayscan,eels,divider,width,risingedge)

    #
    #   Fonctions spécifique au VG
    #

   #void SCAN_EXPORT OrsayScanObjectiveStigmateur(self.orsayscan, double x, double y);
    def ObjectiveStigmateur(self,x,y):
        """ Définit le stigmateur objectif (électrostatique) """
        self.__OrsayScanObjectiveStigmateur(self.orsayscan,x,y)

   #void SCAN_EXPORT OrsayScanObjectiveStigmateurCentre(self.orsayscan, double xcx, double xcy, double ycx, double ycy);
    def ObjectiveStigmateurCentre(self,xcx,xcy,ycx,ycy):
        """ Définit le centre du stigmateur objectif """
        self.__OrsayScanObjectiveStigmateurCentre(self.orsayscan,xcx,xcy,ycx,ycy)

   #void SCAN_EXPORT OrsayScanCondensorStigmateur(self.orsayscan, double x, double y);
    def CondensorStigmateur(self,x,y):
        """ Définit le stigmateur condensuer (magnétique) """
        self.__OrsayScanCondensorStigmateur(self.orsayscan,x,y)

   #void SCAN_EXPORT OrsayScanGrigson(self.orsayscan, double x1, double x2, double y1, double y2);
    def Grigson(self,x1,x2,y1,y2):
        """ Définit le courant Grigson """
        self.__OrsayScanGrigson(self.orsayscan,x1,x2,y1,y2)

   #void SCAN_EXPORT OrsayScanAlObjective(self.orsayscan, double x1, double x2, double y1, double y2);
    def AlObjective(self,x1,x2,y1,y2):
        """ Aligne l'objectif """
        self.__OrsayScanAlObjective(self.orsayscan,x1,x2,y1,y2)

   #void SCAN_EXPORT OrsayScanAlGun(self.orsayscan, double x1, double x2, double y1, double y2);
    def AlGun(self,x1,x2,y1,y2):
        """ Aligne le canon """
        self.__OrsayScanAlGun(self.orsayscan,x1,x2,y1,y2)

   #void SCAN_EXPORT OrsayScanAlStigObjective(self.orsayscan, double x1, double x2, double y1, double y2);
    def AlStigObjective(self,x1,x2,y1,y2):
        """ Aligne le stigmateur canon(?) """
        self.__OrsayScanAlStigObjective(self.orsayscan,x1,x2,y1,y2)

   #void SCAN_EXPORT OrsayScanSetLaser(self.orsayscan, double frequency, int nbpulses, bool bottomblanking, short sync);
    def SetLaser(self,frequency,nbpulses,bottomblanking,sync):
        """ définit le mode de travail du laser
            frquency: frequence des impulsions
            nbpulses: nombre total d'impulsions sur le prochain tir
            bottomblanking: True => utilisé
            sync: < 0 pas utilisé, >= 0 utilise l'entrée choisie pour déclencher l'impulsion
        """
        self.__OrsayScanSetLaser(self.orsayscan,frequency,nbpulses,bottomblanking,sync)

   #void SCAN_EXPORT OrsayScanStartLaser(self.orsayscan, int mode);
    def StartLaser(self, mode, source = -1):
        """
        Démarre le laser
        when mode = 7 => internal generator with frequency defined by SetLaser function
        when mode = 3 => source is taken as trigger, for instance 5 for pixel clock.
        """
        if source == -1:
            self.__OrsayScanStartLaser(self.orsayscan, mode)
        else:
            self.__OrsayScanStartLaserA(self.orsayscan, mode, source)

   #void SCAN_EXPORT OrsayScanCancelLaser(self.orsayscan);
    def CancelLaser(self):
        """ arrete le laser """
        self.__OrsayScanCancelLaser(self.orsayscan)

   #int SCAN_EXPORT OrsayScanGetLaserCount(self.orsayscan);
    def GetLaserCount(self):
        """ donne le nombre d'impulsions déjà faites """
        return self.__OrsayScanGetLaserCount(self.orsayscan)

    # double SCAN_EXPORT OrsayScanGetPMT(self.orsayscan, int index);
    def GetPMT(self,index):
        return self.__OrsayScanGetPMT(self.orsayscan,index)

    # void SCAN_EXPORT OrsayScanSetPMT(self.orsayscan, int index, double value);
    def SetPMT(self, index, value):
        self.__OrsayScanSetPMT(self.orsayscan, index, value)

    # int SCAN_EXPORT OrsayScanCountPMTs (self.orsayscan)
    def CountPMTs(self):
        return self.__OrsayScanCountPMTs(self.orsayscan)

    # bool SCAN_EXPORT OrsayScanGetPMTLimits(self.orsayscan, int index, double &vmin, double & vmax)
    def GetPMTLimits(self, index, vmin, vmax):
        return self.__OrsayScanGetPMTLimits(self.orsayscan, index, vmin, vmax)

    ### END YVES ###

    @property
    def clock_simulation_time(self) -> float:
        """
        Donne le temps par pixel pour le spectre image
        Si == 0: pas de simulation de d'horloge camera,
        Si > 0: l'horloge caméra est générée en interne par scanner.
        """
        return self.__OrsayScanGetClockSimulationTime(self.orsayscan, self.gene)

    @clock_simulation_time.setter
    def clock_simulation_time(self, value: float):
        """
        Donne le temps par pixel pour le spectre image
        Si 0, pas de simulation d'horloge camera.
        """
        self.__OrsayScanSetClockSimulationTime(self.orsayscan, self.gene, value)

    def SetFlybackTime(self, flyback: float) -> float:
        return self.__OrsayScanSetRetourLigne(self.orsayscan, self.gene, flyback)

    def GetFlybackTime(self) -> float:
        return self.__OrsayScanGetRetourLigne(self.orsayscan, self.gene)

