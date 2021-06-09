"""
# -*- coding:utf-8 -*-
Class wrapping the Marcel Tencé dll for controlling an optical spectrometer.
"""
import sys
from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_int, c_long, c_bool, c_double, c_uint64, c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
from shutil import copy2
import os
import logging
import time

__author__  = "Marcel Tence & Mathieu Kociak"
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
    #first copy the extra dll to python folder
    libpath = os.path.dirname(__file__)
    python_folder = sys.executable
    pos = python_folder.find("python.exe")
    if pos>0:
        python_folder=python_folder.replace("python.exe","")
        lib2name=os.path.join(libpath, "../aux_files/DLLs/AttoClient.dll")
        copy2(lib2name,python_folder)

    logging.info(f'Please put AttoClient.dll and '
                 f'SpectroCL.dll at the following folder: {sys.executable}.')

    try:
        libname = os.path.join(libpath, "C:/Monch_plugins/swift-spectro/nionswift_plugin/spectro/SpectroCL.dll")
        _library = cdll.LoadLibrary(libname)
    except FileNotFoundError:
        libname = os.path.join(libpath, "../aux_files/DLLs/SpectroCL.dll")
        _library = cdll.LoadLibrary(libname)
    except OSError:
        libname = os.path.join(libpath, "../aux_files/DLLs/SpectroCL.dll")
        _library = cdll.LoadLibrary(libname)

    logging.info(f"Orsay SpectroCL library: {_library}")
else:
    raise Exception("It must a python 64 bit version")
    

    # void (*SendMyMessage)(int kind):#CHECK: 
SENDMYMESSAGEFUNC = WINFUNCTYPE(None, c_int)
SENDMIRRORMESSAGEFUNC = WINFUNCTYPE(None, c_char_p)
    # void MONOCL_EXPORT *OrsayMonoCLInit(int manufacturer, int portnb, void(*sendmessage)(int kind)):
_OrsayMonoCLInit=_buildFunction(_library.OrsayMonoCLInit,[c_int,c_int,SENDMYMESSAGEFUNC], c_void_p)
    #void MONOCL_EXPORT *OrsayMonoCLMirrorInit(int manufacturer, int portnb, void(*sendmessage)(int kind), void(*sendmirrormessage)(const char *message));
_OrsayMonoCLWithMirrorInit=_buildFunction(_library.OrsayMonoCLMirrorInit,[c_int,c_int,SENDMYMESSAGEFUNC,SENDMIRRORMESSAGEFUNC], c_void_p)
#CHECK: bonne forme pour SENDMYMESSAGEFUNC?
    # void MONOCL_EXPORT OrsayMonoCLClose(void* o):
_OrsayMonoCLClose=_buildFunction(_library.OrsayMonoCLClose,[c_void_p], None)
    #

    #
    # void MONOCL_EXPORT SendWaveLength(self, double value):
_SendWaveLength=_buildFunction(_library.SendWaveLength,[c_void_p, c_double], None)
    # void MONOCL_EXPORT SendGrating(self, int number):
_SendGrating=_buildFunction(_library.SendGrating,[c_void_p, c_int], None)
    # void MONOCL_EXPORT SendReinit(self):
#NOT IMPLEMENTED
    # void MONOCL_EXPORT SendSlitEntranceFront(self, double value):
_SendSlitEntranceFront=_buildFunction(_library.SendSlitEntranceFront,[c_void_p, c_double], None)
    # void MONOCL_EXPORT SendSlitEntranceSide(self, double value):
_SendSlitEntranceSide=_buildFunction(_library.SendSlitEntranceSide,[c_void_p,c_double], None)
    # void MONOCL_EXPORT SendSlitExitFront(self, double value):
_SendSlitExitFront=_buildFunction(_library.SendSlitExitFront,[c_void_p,c_double], None)
    # void MONOCL_EXPORT SendSlitExitSide(self, double value):
_SendSlitExitSide=_buildFunction(_library.SendSlitExitSide,[c_void_p,c_double], None)
    # void MONOCL_EXPORT SendStatusUpdate(self):
_SendStatusUpdate=_buildFunction(_library,[c_void_p], None)
    # void MONOCL_EXPORT SendSwitchToAxialEntry(self):
_SendSwitchToAxialEntry=_buildFunction(_library.SendSwitchToAxialEntry,[c_void_p], None)
    # void MONOCL_EXPORT SendSwitchToLateralEntry(self):
_SendSwitchToLateralEntry=_buildFunction(_library.SendSwitchToLateralEntry,[c_void_p], None)
    # double MONOCL_EXPORT GetCurrentWaveLength(self):
_GetCurrentWaveLength=_buildFunction(_library.GetCurrentWaveLength,[c_void_p], c_double)
    # int MONOCL_EXPORT GetCurrentGroove(void *o):
_GetCurrentGroove=_buildFunction(_library.GetCurrentGroove,[c_void_p], c_int)
    # void MONOCL_EXPORT InitSpectro(self, int portnb):
_InitSpectro=_buildFunction(_library.InitSpectro,[c_void_p,c_int], c_void_p)
    # const MONOCL_EXPORT char *gratingText(self, int number):
_gratingText=_buildFunction(_library.gratingText,[c_void_p,c_int], c_char_p)
    # double MONOCL_EXPORT GetCLSpectrumRange(self, double pixelWidth, int nbPixels):
_GetCLSpectrumRange=_buildFunction(_library.GetCLSpectrumRange,[c_void_p, c_double,c_int], c_double)
    # double MONOCL_EXPORT GetCLSpectrumCenter(self):
_GetCLSpectrumCenter=_buildFunction(_library.GetCLSpectrumCenter,[c_void_p], c_double)
    #
    # int MONOCL_EXPORT IsReady(self):
_IsReady=_buildFunction(_library.IsReady,[c_void_p], c_int)
    #
    # bool MONOCL_EXPORT IsConnected(self):
_IsConnected=_buildFunction(_library.IsConnected,[c_void_p], c_bool)
    # void (*statusUpdateA)(double waveLenght, int slitEntranceFront, int slitExitSide, int grating, int exitMirror):
STATUSUPDATEA= WINFUNCTYPE(None,c_double,c_int,c_int,c_int,c_int)#CHECK: pointer to a function!!! and not reused...
#_statusUpdateA=_buildFunction(_library,[c_double,c_int,c_int,c_int,c_int],c_void_p)
    # const char MONOCL_EXPORT *spectroModel(self):
_spectroModel=_buildFunction(_library.spectroModel,[c_void_p], c_char_p)
    # int MONOCL_EXPORT nbgratings(self):
_nbgratings=_buildFunction(_library.nbgratings,[c_void_p], c_int)
    # int MONOCL_EXPORT grating(self):
_grating=_buildFunction(_library.grating,[c_void_p], c_int)
    # const char MONOCL_EXPORT *GratingsNames(self, int gr):
_GratingsNames=_buildFunction(_library.GratingsNames,[c_void_p,c_int], c_char_p)
    # double MONOCL_EXPORT Centre(self):
_Centre=_buildFunction(_library.Centre,[c_void_p], c_double)
    # int MONOCL_EXPORT exitMirror(self):
_exitMirror=_buildFunction(_library.exitMirror,[c_void_p], c_int)
    # bool MONOCL_EXPORT hasEntranceAxialSlit(self):
_hasEntranceAxialSlit=_buildFunction(_library.hasEntranceAxialSlit,[c_void_p], c_bool)
    # bool MONOCL_EXPORT hasEntranceSideSlit(self):
_hasEntranceSideSlit=_buildFunction(_library.hasEntranceSideSlit,[c_void_p], c_bool)
    # bool MONOCL_EXPORT hasExitAxialSlit(self):
_hasExitAxialSlit=_buildFunction(_library.hasExitAxialSlit,[c_void_p], c_bool)
    # bool MONOCL_EXPORT hasExitSideSlit(self):
_hasExitSideSlit=_buildFunction(_library.hasExitSideSlit,[c_void_p], c_bool)
    # double MONOCL_EXPORT EntranceAxialSlitValue(self):
_EntranceAxialSlitValue=_buildFunction(_library.EntranceAxialSlitValue,[c_void_p], c_double)
    # double MONOCL_EXPORT EntranceSideSlitValue(self):
_EntranceSideSlitValue=_buildFunction(_library.EntranceSideSlitValue,[c_void_p],c_double)
    # double MONOCL_EXPORT ExitAxialSlitValue(self):
_ExitAxialSlitValue=_buildFunction(_library.ExitAxialSlitValue,[c_void_p],c_double)
    # double MONOCL_EXPORT ExitSideSlitValue(self):
_ExitSideSlitValue=_buildFunction(_library.ExitSideSlitValue,[c_void_p],c_double)

_MirrorSendCommand=_buildFunction(_library.MirrorSendCommand, [c_void_p, c_char_p], None)

class OptSpectrometer:
    """ class wrapping the spectrometer class from CMonoCL.dll
    requires CMonoCL.dll to run """
    
    def __init__(self, sendmessage:callable, manufacturer=2, portnb=6, sendmirrormessage=None)->None:
        """
        sendmessage is a python callback you provide to the dll. The callback will be called when some property of the spectro is actullay set, afer a "send" method has been called
        the integer value gives the type of property being set
        10+1:grating #
        10+2:wavelength
        10+3:slit entrance front
        10+4:slit entrance side
        10+5: slit exit front
        10+6:slit exit side
        sendmessage is likely to be a method from a delegate object
        """
        # void MONOCL_EXPORT *OrsayMonoCLInit(int manufacturer, int portnb, void(*sendmessage)(int kind)):
        # manufacturer
        #   1 Acton
        #   2 Attolight (pas encore testé)
        #  -1 Acton simulé.
        if sendmirrormessage is None:
            self.OrsayMonoCL=_OrsayMonoCLInit(manufacturer, portnb, sendmessage)
        else:
            self.OrsayMonoCL=_OrsayMonoCLWithMirrorInit(manufacturer, portnb, sendmessage, sendmirrormessage)

        self.sendmessage = sendmessage
                
    def OrsayMonoCLCLose(self) -> None:
        _OrsayMonoCLClose(self.OrsayMonoCL)
        # force reference to dll to be null.
        self.OrsayMonoCL = 0
        #
    def SendWaveLength(self,wavelength:float) -> None:
        _SendWaveLength(self.OrsayMonoCL,wavelength)
        #
    def SendGrating(self, gratingnumber:float)-> None:
        _SendGrating(self.OrsayMonoCL,gratingnumber)
        
    def SendSlitEntranceFront(self,value:float)->None:
        _SendSlitEntranceFront(self.OrsayMonoCL, value)
        
    def SendSlitEntranceSide(self,value:float)->None:
        _SendSlitEntranceSide(self.OrsayMonoCL,value)

    def SendSlitExitFront(self,value:float)-> None:
        _SendSlitExitFront(self.OrsayMonoCL, value)
        
    def SendSlitExitSide(self,value: float) -> None:
        _SendSlitExitSide(self.OrsayMonoCL, value)
        
    def SendStatusUpdate(self) -> None:
        _SendStatusUpdate(self.OrsayMonoCL)
        
    def SendSwitchToAxialEntry(self) -> None:
        _SendSwitchToAxialEntry(self.OrsayMonoCL)

    def SendSwitchToLateralEntry(self) -> None:
        _SendSwitchToLateralEntry(self.OrsayMonoCL)
        
    def GetCurrentWaveLength(self) -> float:
        return _GetCurrentWaveLength(self.OrsayMonoCL)
        
    def GetCurrentGroove(self) -> int:
        return _GetCurrentGroove(self.OrsayMonoCL)

    def InitSpectro(self,portnb:int) -> None:#CHECK: where to call this init? in the __init__ of this function, or from the "spectrodevice"?
        _InitSpectro(self.OrsayMonoCL,portnb)
        
    def gratingText(self,number: int) -> str:
        return _convertToString23(_gratingText(self.OrsayMonoCL,number))
        
    def GetCLSpectrumRange(self,pixelWidth: float,nbPixels: int) -> float:
        return _GetCLSpectrumRange(self.OrsayMonoCL,pixelWidth,nbPixels)
        
    def GetCLSpectrumCenter(self) -> float:
        return _GetCLSpectrumCenter(self.OrsayMonoCL)
        #
    def IsReady(self) -> int:
        return _IsReady(self.OrsayMonoCL)
        #
    def IsConnected(self) -> bool:
        return _IsConnected(self.OrsayMonoCL)
        # void (*statusUpdateA)(double waveLenght, int slitEntranceFront, int slitExitSide, int grating, int exitMirror):
    #STATUSUPDATEA= WINFUNCTYPE(None,c_double,c_int,c_int,c_int,c_int)#CHECK: pointer to a function!!! and not reused...
    #_statusUpdateA=_buildFunction(_library,[c_double,c_int,c_int,c_int,c_int],c_void_p)

    def spectroModel(self) -> str:
        return _spectroModel(self.OrsayMonoCL)
        
    def nbgratings(self) -> int:
        return _nbgratings(self.OrsayMonoCL)
        
    def grating(self) -> int:
        return _grating(self.OrsayMonoCL)
    
    def GratingsNames(self, grating:int)-> str:
        return _GratingsNames(self.OrsayMonoCL,grating)
        
    def Centre(self) -> float:
        return _Centre(self.OrsayMonoCL)
        
    def exitMirror(self) -> int:
        return _exitMirror(self.OrsayMonoCL)
        
    def hasEntranceAxialSlit(self) -> bool:
        return _hasEntranceAxialSlit(self.OrsayMonoCL)
        
    def hasEntranceSideSlit(self) -> bool:
        return _hasEntranceSideSlit(self.OrsayMonoCL)
        
    def hasExitAxialSlit(self) -> bool:
        return _hasExitAxialSlit(self.OrsayMonoCL)
        
    def hasExitSideSlit(self) -> bool:
        return _hasExitSideSlit(self.OrsayMonoCL)
        
    def EntranceAxialSlitValue(self):
        return _EntranceAxialSlitValue(self.OrsayMonoCL)
        
    def EntranceSideSlitValue(self):
        return _EntranceSideSlitValue(self.OrsayMonoCL)
        
    def ExitAxialSlitValue(self):
        return _ExitAxialSlitValue(self.OrsayMonoCL)
        
    def ExitSideSlitValue(self):
        return _ExitSideSlitValue(self.OrsayMonoCL)
    
    def MirrorSend(self, command:str):
        return _MirrorSendCommand(self.OrsayMonoCL,command.encode('ascii'))

    ## Second Version. Compatible with VG Lumiere and ChromaTEM

    def gratingLPMM(self):
        lpmms = list()
        for i in range(3):
            lpmms.append(float(self.GratingsNames(i).decode().split('g/mm')[0]))
        return lpmms

    def gratingNames(self):
        grat = list()
        for i in range(3):
            grat.append(self.GratingsNames(i).decode())
        return grat

    def get_wavelength(self):
        wav = self.GetCurrentWaveLength()*1e9
        return wav

    def set_wavelength(self, wl):
        self.SendWaveLength(wl*1e-9)
        return True

    def get_grating(self):
        return self.grating()

    def set_grating(self, value):
        self.SendGrating(value)
        return True

    def get_exit(self):
        return self.EntranceSideSlitValue()*1e6

    def set_exit(self, value):
        self.SendSlitEntranceSide(value*1e-6)
        self.sendmessage(14)
        return True

    def get_entrance(self):
        return self.EntranceAxialSlitValue()*1e6

    def set_entrance(self, value):
        self.SendSlitEntranceFront(value*1e-6)
        return True

    def get_which(self):
        return self.exitMirror()

    def set_which(self, value):
        if value==0: #AXIAL
            self.SendSwitchToAxialEntry()
        elif value==1: #LATERAL
            self.SendSwitchToLateralEntry()

    def get_specFL(self):
        return 320.0

    def which_camera(self):
        return 'orsay_camera_eireB'

    def camera_pixels(self):
        return 1600

    def deviation_angle(self):
        return 0.34