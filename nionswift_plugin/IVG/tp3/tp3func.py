import json
import requests
import threading
import logging
import queue
import socket
import numpy
import struct
import pathlib
import os
import select

from nion.swift.model import HardwareSource
#from swift_rust.target.release import rust2swift

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc


class Response():
    def __init__(self):
        self.text = '***TP3***: This is simul mode.'


SAVE_FILE = False


class TimePix3():

    def __init__(self, url, simul, message):

        fst_string = url.find('http://')
        assert fst_string==0, "***TP3***: Put ip_address in the form of 'http://IP:PORT'."
        sec_string = url.find(':', fst_string+7)

        self.success = False
        self.__serverURL = url
        self.__camIP = url[fst_string+7:sec_string]
        self.__dataQueue = queue.LifoQueue()
        self.__eventQueue = queue.Queue()
        self.__spimData = None
        self.__isPlaying = False
        self.__softBinning = False
        self.__isCumul = False
        self.__tr = False
        self.__expTime = None
        self.__port = 0
        self.__delay = 0.
        self.__width = 0.
        self.__tdc = 0  # Beginning of line n and beginning of line n+1
        self.__tp3mode = 0
        self.__filepath = os.path.join(pathlib.Path(__file__).parent.absolute(), "data")
        self.__simul = simul
        self.sendmessage = message

        if not simul:
            try:
                initial_status_code = self.status_code()
                if initial_status_code == 200:
                    logging.info('***TP3***: Timepix has initialized correctly.')
                else:
                    logging.info('***TP3***: Problem initializing Timepix3. Bad status code.')

                # Loading bpc and dacs
                bpcFile = '/home/asi/load_files/tpx3-demo.bpc'
                dacsFile = '/home/asi/load_files/tpx3-demo.dacs'
                self.cam_init(bpcFile, dacsFile)
                self.acq_init(99999)
                self.set_destination(self.__port)
                logging.info(f'***TP3***: Current detector configuration is {self.get_config()}.')
                self.success = True
            except:
                logging.info('***TP3***: Problem initializing Timepix3. Cannot load files.')
        else:
            logging.info('***TP3***: Timepix3 in simulation mode.')

    def request_get(self, url):
        if not self.__simul:
            resp = requests.get(url=url)
            return resp
        else:
            resp = Response()
            return resp

    def request_put(self, url, data):
        if not self.__simul:
            resp = requests.put(url=url, data=data)
            return resp
        else:
            resp = Response()
            return resp

    def status_code(self):
        """
        Status code 200 is good. Other status code meaning can be seen in serval manual.
        """
        try:
            resp = self.request_get(url=self.__serverURL)
        except requests.exceptions.RequestException as e:  # Exceptions handling example
            return -1
        status_code = resp.status_code
        return status_code

    def dashboard(self):
        """
        Dashboard description can be seen in manual
        """
        resp = self.request_get(url=self.__serverURL + '/dashboard')
        data = resp.text
        dashboard = json.loads(data)
        return dashboard

    def cam_init(self, bpc_file, dacs_file):
        """
        This load both binary pixel config file and dacs.
        """
        resp = self.request_get(url=self.__serverURL + '/config/load?format=pixelconfig&file=' + bpc_file)
        data = resp.text
        logging.info(f'***TP3***: Response of loading binary pixel configuration file: ' + data)

        resp = self.request_get(url=self.__serverURL + '/config/load?format=dacs&file=' + dacs_file)
        data = resp.text
        logging.info(f'***TP3***: Response of loading dacs file: ' + data)

    def get_config(self):
        """
        Gets the entire detector configuration. Check serval manual to a full description.
        """
        if not self.__simul:
            resp = self.request_get(url=self.__serverURL + '/detector/config')
            data = resp.text
            detectorConfig = json.loads(data)
        else:
            detectorConfig = \
                {'Fan1PWM': 100, 'Fan2PWM': 100, 'BiasVoltage': 100, 'BiasEnabled': True, 'TriggerIn': 2,
                 'TriggerOut': 0,
                 'Polarity': 'Positive', 'TriggerMode': 'AUTOTRIGSTART_TIMERSTOP', 'ExposureTime': 0.05,
                 'TriggerPeriod': 0.05, 'nTriggers': 99999, 'PeriphClk80': False, 'TriggerDelay': 0.0,
                 'Tdc': ['P0', 'P0'], 'LogLevel': 1}
        return detectorConfig

    def acq_init(self, ntrig=99999):
        """
        Initialization of detector. Standard value is 99999 triggers in continuous mode (a single trigger).
        """
        detector_config = self.get_config()
        detector_config["nTriggers"] = ntrig
        detector_config["TriggerMode"] = "CONTINUOUS"
        # detector_config["TriggerMode"] = "AUTOTRIGSTART_TIMERSTOP"
        detector_config["BiasEnabled"] = True
        detector_config["TriggerPeriod"] = 1.0  # 1s
        detector_config["ExposureTime"] = 1.0  # 1s
        detector_config["Tdc"] = ['PN0', 'PN0']

        resp = self.request_put(url=self.__serverURL + '/detector/config', data=json.dumps(detector_config))
        data = resp.text
        logging.info('Response of updating Detector Configuration: ' + data)

    def set_destination(self, port):
        """
        Sets the destination of the data. Data modes in ports are also defined here. Note that you always have
        data flown in port 8088 and 8089 but only one client at a time.
        """
        options = self.getPortNames()
        if port==0:
            destination = {
                "Raw": [{
                    "Base": "tcp://127.0.0.1:8098",
                }]
            }
        elif port == 1:
            destination = {
                "Raw": [{
                    "Base": "file:/home/asi/load_files/data",
                    "FilePattern": "raw",
                }]
            }
        elif port == 2:
            destination = {
                "Image": [{
                    "Base": "tcp://127.0.0.1:8088",
                    "Format": "jsonimage",
                    "Mode": "count",
                }]
            }
        elif port == 3:
            destination = {
                "Image": [{
                    "Base": "tcp://127.0.0.1:8088",
                    "Format": "jsonimage",
                    "Mode": "tot",
                }]
            }
        resp = self.request_put(url=self.__serverURL + '/server/destination', data=json.dumps(destination))
        data = resp.text
        logging.info('***TP3***: Response of uploading the Destination Configuration to SERVAL : ' + data)
        logging.info(f'***TP3***: Selected port is {port} and corresponds to: ' + options[port])

    def getPortNames(self):
        return ['TCP Stream', 'Save Locally', 'JSON Image (counts)', 'JSON Image (ToT)']

    def getCCDSize(self):
        return (256, 1024)

    def getSpeeds(self, port):
        return list(['Unique'])

    def getGains(self, port):
        return list(['Unique'])

    def getBinning(self):
        return (1, 1)

    def setBinning(self, bx, by):
        pass

    def getImageSize(self):
        return (1024, 256)

    def registerLogger(self, fn):
        pass

    def addConnectionListener(self, fn):
        pass

    @property
    def simulation_mode(self) -> bool:
        return self.__simul

    def registerDataLocker(self, fn):
        pass

    def registerDataUnlocker(self, fn):
        pass

    def registerSpimDataLocker(self, fn):
        pass

    def registerSpimDataUnlocker(self, fn):
        pass

    def registerSpectrumDataLocker(self, fn):
        pass

    def registerSpectrumDataUnlocker(self, fn):
        pass

    def setCCDOverscan(self, sx, sy):
        pass

    def displayOverscan(self, displayed):
        pass

    def setMirror(self, mirror):
        pass

    def setAccumulationNumber(self, count):
        pass

    def getAccumulateNumber(self):
        pass

    def setSpimMode(self, mode):
        pass

    def startSpim(self, nbspectra, nbspectraperpixel, dwelltime, is2D):
        """
        Similar to startFocus. Just to be consistent with VGCameraYves. Message=02 because of spim.
        """
        try:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 2, 7)  # Copy Line Start
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 2, 13)  # Copy line 05
        except AttributeError:
            logging.info("***TP3***: Could not set TDC to spim acquisition.")
        port = 8088
        self.__softBinning = True
        message = 2
        self.__isCumul = False
        if self.getCCDStatus() == "DA_RECORDING":
            self.stopFocus()
        if self.getCCDStatus() == "DA_IDLE" and (self.__tp3mode == 2 or self.__tp3mode == 3 or
                                                 self.__tp3mode == 4):
            resp = self.request_get(url=self.__serverURL + '/measurement/start')
            data = resp.text
            self.start_listening(port, message=message, spim=nbspectra)
            return True
        else:
            logging.info('***TP3***: Check if experiment type matches mode selection.')

    def pauseSpim(self):
        pass

    def resumeSpim(self, mode):
        pass

    def stopSpim(self, immediate):
        """
        Identical to stopFocus. Just to be consistent with VGCameraYves.
        """
        try:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 0, 0)
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 0, 0)
        except AttributeError:
            logging.info("***TP3***: Could not turn off TDC after spim acquisition.")
        status = self.getCCDStatus()
        resp = self.request_get(url=self.__serverURL + '/measurement/stop')
        data = resp.text
        self.finish_listening()

        if self.__tr:
            logging.info(f'***TP3***: TR is on. Cancelling Laser.')
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            LaserInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("sgain_controller")
            if LaserInstrument is not None and not self.__simul: LaserInstrument.over_spim_TP3()

    def isCameraThere(self):
        return True

    def getTemperature(self):
        pass

    def setTemperature(self, temperature):
        pass

    def setupBinning(self):
        pass

    def setTdc01(self, index, **kargs):
        if self.__simul: return
        if index == 0:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 0, 0)
        if index == 1:  # Internal Generator
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 7, 0, period=exposure)
        if index == 2:  # Start of Line
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 2, 7)  # Copy Line Start

    def setTdc02(self, index, **kargs):
        if self.__simul: return
        if index == 0:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 0, 0)
        if index == 1:  # Laser Line. Copying an output.
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 7, 0, period=exposure)
        if index == 2:  # High Tension. Copying an input.
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 2, 3, period=0.000050, on_time=0.000045)

    def startFocus(self, exposure, displaymode, accumulate):
        """
        Start acquisition. Displaymode can be '1d' or '2d' and regulates the global attribute self.__softBinning.
        accumulate is 1 if Cumul and 0 if Focus. You use it to chose to which port the client will be listening on.
        Message=1 because it is the normal data_locker.
        """
        #if not self.__simul:
        try:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 7, 0, period=exposure)
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 2, 13)  # Copy Line 05
            # scanInstrument.scan_device.orsayscan.SetTdcLine(0, 2, 3, period=0.000050, on_time=0.000045) # Copy Line 05
        except AttributeError:
            logging.info("***TP3***: Cannot find orsay scan hardware. Tdc is not properly setted.")
        port = 8088
        self.__softBinning = True if displaymode == '1d' else False
        message = 1
        self.__isCumul = bool(accumulate)
        if self.getCCDStatus() == "DA_RECORDING":
            self.stopFocus()
        if self.getCCDStatus() == "DA_IDLE" and (self.__tp3mode == 0 or self.__tp3mode == 1):
            resp = self.request_get(url=self.__serverURL + '/measurement/start')
            data = resp.text
            self.start_listening(port, message=message)
            return True
        else:
            logging.info('***TP3***: Check if experiment type matches mode selection.')

    def stopFocus(self):
        """
        Stop acquisition. Finish listening put global isPlaying to False and wait client thread to finish properly using
        .join() method. Also replaces the old Queue with a new one with no itens on it (so next one won't use old data).
        """
        try:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            scanInstrument.scan_device.orsayscan.SetTdcLine(1, 0, 0)
            scanInstrument.scan_device.orsayscan.SetTdcLine(0, 0, 0)
        except AttributeError:
            logging.info("***TP3***: Cannot find orsay scan hardware. Tdc is not properly turned down.")
        status = self.getCCDStatus()
        resp = self.request_get(url=self.__serverURL + '/measurement/stop')
        data = resp.text
        self.finish_listening()

    def setExposureTime(self, exposure):
        """
        Set camera exposure time.
        """
        self.__expTime = exposure

    def setDelayTime(self, delay):
        self.__delay = delay

    def setWidthTime(self, width):
        self.__width = width

    def setTp3Mode(self, mode):
        self.__tp3mode = mode

    def getNumofSpeeds(self, cameraport):
        pass

    def getCurrentSpeed(self, cameraport):
        return 0

    def getAllPortsParams(self):
        return None

    def setSpeed(self, cameraport, speed):
        pass

    def getNumofGains(self, cameraport):
        pass

    def getGain(self, cameraport):
        return 0

    def getGainName(self, cameraport, gain):
        pass

    def setGain(self, gain):
        pass

    def getReadoutTime(self):
        return 0

    def getNumofPorts(self):
        pass

    def getPortName(self, portnb):
        pass

    def getCurrentPort(self):
        if self.__port is not None:
            return self.__port
        else:
            return 0

    def setCurrentPort(self, cameraport):
        self.__port = cameraport
        self.set_destination(cameraport)

    def getMultiplication(self):
        return [1]

    def setMultiplication(self, multiplication):
        pass

    def getCCDStatus(self) -> dict():
        '''
        Returns
        -------
        str

        Notes
        -----
        DA_IDLE is idle. DA_PREPARING is busy to setup recording. DA_RECORDING is busy recording
        and output data to destinations. DA_STOPPING is busy to stop the recording process
        '''
        if not self.__simul:
            dashboard = json.loads(self.request_get(url=self.__serverURL + '/dashboard').text)
            if dashboard["Measurement"] is None:
                return "DA_IDLE"
            else:
                return dashboard["Measurement"]["Status"]
        else:
            value = "DA_RECORDING" if self.__isPlaying else "DA_IDLE"
            return value

    def getReadoutSpeed(self):
        pass

    def getPixelTime(self, cameraport, speed):
        pass

    def adjustOverscan(self, sizex, sizey):
        pass

    def setTurboMode(self, active, sizex, sizey):
        pass

    def getTurboMode(self):
        return [0]

    def setExposureMode(self, mode, edge):
        pass

    def getExposureMode(self):
        pass

    def setPulseMode(self, mode):
        pass

    def setVerticalShift(self, shift, clear):
        pass

    def setFan(self, On_Off: bool):
        pass

    def getFan(self):
        return False

    def setArea(self, area: tuple):
        pass

    def getArea(self):
        return (0, 0, 256, 1024)

    def setVideoThreshold(self, threshold):
        pass

    def getVideoThreshold(self):
        pass

    def setCCDOverscan(self, sx, sy):
        pass

    """
    --->Functions of the client listener<---
    """

    def start_listening(self, port=8088, message=1, spim=1):
        """
        Starts the client Thread and sets isPlaying to True.
        """
        self.__isPlaying = True
        self.__clientThread = threading.Thread(target=self.acquire_streamed_frame, args=(port, message, spim,))
        self.__clientThread.start()

    def finish_listening(self):
        """
        .join() the client Thread, puts isPlaying to false and replaces old queue to a new one with no itens on it.
        """
        if self.__isPlaying:
            self.__isPlaying = False
            self.__clientThread.join()
            logging.info(f'***TP3***: Stopping acquisition. There was {self.__dataQueue.qsize()} items in the Queue.')
            logging.info(
                f'***TP3***: Stopping acquisition. There was {self.__eventQueue.qsize()} electron events in the Queue.')
            self.__dataQueue = queue.LifoQueue()
            self.__eventQueue = queue.Queue()

    def acquire_streamed_frame(self, port, message, spim):
        """
        Main client function. Main loop is explained below.

        Client is a socket connected to camera in host computer 129.175.108.52. Port depends on which kind of data you
        are listening on. After connection, timeout is set to 5 ms, which is camera current dead time. cam_properties
        is a dict containing all info camera sends through tcp (the header); frame_data is the frame; buffer_size is how
        many bytes we collect within each loop interaction; frame_number is the frame counter and frame_time is when the
        whole frame began.

        check string value is a convenient function to detect the values using the header standard format for jsonimage.
        """
        inputs = list()
        outputs = list()
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_aux = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #if self.__simul:
        client_aux.bind(("127.0.0.1", 9088))
        #else:
        #    client_aux.bind(("192.168.199.10", 9088))
        """
        127.0.0.1 -> LocalHost;
        129.175.108.58 -> Patrick;
        129.175.81.162 -> My personal Dell PC;
        192.0.0.11 -> My old personal (outside lps.intra);
        192.168.199.11 -> Cheetah (to VG Lum. Outisde lps.intra);
        129.175.108.52 -> CheeTah
        """
        ip = socket.gethostbyname('127.0.0.1') if self.__simul else socket.gethostbyname(self.__camIP)
        address = (ip, port)
        try:
            client.connect(address)
            logging.info(f'***TP3***: Both clients connected over {ip}:{port}.')
            inputs.append(client)
            inputs.append(client_aux)
        except ConnectionRefusedError:
            return False

        cam_properties = dict()
        buffer_size = 64000

        config_bytes = b''

        self.__tr = False  # Start always with false and will be updated if otherwise

        if self.__softBinning:
            config_bytes += b'\x01'  # Soft binning
            if self.__tp3mode == 5:
                config_bytes += b'\x01'  # Bit depth 16 when saving SPIM locally
            else:
                config_bytes += b'\x02'  # Bit depth 32 otherwise
        else:
            config_bytes += b'\x00'  # No soft binning
            config_bytes += b'\x01'  # Bit depth is 16

        if self.__isCumul:
            config_bytes += b'\x01'  # Cumul is ON
        else:
            config_bytes += b'\x00'  # Cumul is OFF

        config_bytes += bytes([self.__tp3mode])
        if message == 1:
            size = 1
            config_bytes += size.to_bytes(2, 'big')
            config_bytes += size.to_bytes(2, 'big')

        elif message == 2:
            self.__spimData = numpy.zeros(spim * 1025, dtype=numpy.uint32)
            self.__xspim = int(numpy.sqrt(spim))
            self.__yspim = int(numpy.sqrt(spim))

            if self.__tp3mode == 3:  # Time Resolved SPIM
                if not self.__simul:
                    scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                        "orsay_scan_device")
                    LaserInstrument = HardwareSource.HardwareSourceManager().get_instrument_by_id("sgain_controller")
                    pixel_time = int(scanInstrument.scan_device.current_frame_parameters['pixel_time_us'])
                    if pixel_time == 100.0 and LaserInstrument:
                        self.__tr = True
                        logging.info(f'***TP3***: TR is True. Setting laser controlled by pixel clock.')
                        LaserInstrument.prepare_spim_TP3()
                    else:
                        logging.info(f'***TP3***: Pixel time is not 100 us || LaserInstrument was not found.')
                else:
                    self.__tr = True

            config_bytes += self.__xspim.to_bytes(2, 'big')
            config_bytes += self.__yspim.to_bytes(2, 'big')
            self.sendmessage(message)

        try:
            scanInstrument = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                "orsay_scan_device")
            if scanInstrument.scan_device.current_frame_parameters['subscan_pixel_size']:
                x_size = int(scanInstrument.scan_device.current_frame_parameters['subscan_pixel_size'][0])
                y_size = int(scanInstrument.scan_device.current_frame_parameters['subscan_pixel_size'][1])
            else:
                x_size = int(scanInstrument.scan_device.current_frame_parameters['size'][0])
                y_size = int(scanInstrument.scan_device.current_frame_parameters['size'][1])
            config_bytes += x_size.to_bytes(2, 'big')
            config_bytes += y_size.to_bytes(2, 'big')
        except AttributeError:
            logging.info("***TP3***: Could not grab scan parameters. Sending (64, 64) to TP3.")
            config_bytes += struct.pack(">H", 64)
            config_bytes += struct.pack(">H", 64)

        config_bytes += struct.pack(">d", self.__delay)  # BE. See https://docs.python.org/3/library/struct.html
        config_bytes += struct.pack(">d", self.__width)  # BE. See https://docs.python.org/3/library/struct.html

        client.send(config_bytes)

        def check_string_value(header, prop):
            """
            Check the value in the header dictionary. Some values are not number so a valueError
            exception handles this.
            """

            start_index = header.index(prop)
            end_index = start_index + len(prop)
            begin_value = header.index(':', end_index, len(header)) + 1
            if prop == 'height':
                end_value = header.index('}', end_index, len(header))
            else:
                end_value = header.index(',', end_index, len(header))
            try:
                if prop == 'timeAtFrame':
                    value = float(header[begin_value:end_value])
                else:
                    value = int(header[begin_value:end_value])
            except ValueError:
                value = str(header[begin_value:end_value])
            return value

        def put_queue(cam_prop, frame):
            try:
                assert int(cam_properties['width']) * int(
                    cam_properties['height']) * int(
                    cam_properties['bitDepth'] / 8) == int(cam_properties['dataSize'])
                assert cam_properties['dataSize'] + 1 == len(frame)
                self.__dataQueue.put((cam_prop, frame))
                self.sendmessage(message)
                return True
            except AssertionError:
                logging.info(
                    f'***TP3***: Problem in size/len assertion. Properties are {cam_properties} and data is {len(frame)}')
                return False

        if message == 1:
            while True:
                try:
                    read, _, _ = select.select(inputs, outputs, inputs)
                    for s in read:
                        if s == client:
                            packet_data = client.recv(buffer_size)
                            if packet_data == b'': return
                            while (packet_data.find(b'{"time') == -1) or (packet_data.find(b'}\n') == -1):
                                temp = client.recv(buffer_size)
                                if temp == b'':
                                    return
                                else:
                                    packet_data += temp

                            begin_header = packet_data.index(b'{"time')
                            end_header = packet_data.index(b'}\n', begin_header)
                            header = packet_data[begin_header:end_header + 1].decode('latin-1')
                            for properties in ["timeAtFrame", "frameNumber", "measurementID", "dataSize", "bitDepth",
                                               "width",
                                               "height"]:
                                cam_properties[properties] = (check_string_value(header, properties))

                            data_size = int(cam_properties['dataSize'])

                            while len(packet_data) < begin_header + data_size + len(header):
                                temp = client.recv(buffer_size)
                                if temp == b'':
                                    return
                                else:
                                    packet_data += temp

                            # frame_data += packet_data[:begin_header]
                            # if put_queue(cam_properties, frame_data):
                            #    frame_data = b''
                            # if not frame_data:
                            frame_data = packet_data[end_header + 2:end_header + 2 + data_size + 1]
                            if put_queue(cam_properties, frame_data):
                                frame_data = b''
                        elif s==client_aux: #UDP Packet
                            pass

                except ConnectionResetError:
                    logging.info("***TP3***: Socket reseted. Closing connection.")
                    return
                if not self.__isPlaying:
                    return

        elif message == 2:
            while True:
                try:
                    read, _, _ = select.select(inputs, outputs, inputs)
                    for s in read:
                        if s == client:
                            packet_data = client.recv(buffer_size)
                            if packet_data == b'':
                                logging.info('***TP3***: No more packets received in SPIM.')
                                self.update_spim_all()
                                return

                            #rust2swift.update_spim(packet_data)

                            dt = numpy.dtype(numpy.uint32).newbyteorder('>')
                            event_list = numpy.frombuffer(packet_data, dtype=dt)
                            self.__eventQueue.put(event_list)

                            if len(packet_data) < buffer_size / 2:
                                self.update_spim()
                        elif s==client_aux: #UDP Packet
                            pass

                except ConnectionResetError:
                    logging.info("***TP3***: Socket reseted. Closing connection.")
                    return

                if not self.__isPlaying:
                    logging.info('***TP3***: Finishing SPIM.')
                    self.update_spim_all()
                    return
        return

    def get_last_data(self):
        return self.__dataQueue.get()

    def get_last_event(self):
        return self.__eventQueue.get()

    def update_spim(self):
        event_list = self.__eventQueue.get()
        unique, counts = numpy.unique(event_list, return_counts=True)
        counts = counts.astype(numpy.uint32)
        self.__spimData[unique] += counts

    def update_spim_all(self):
        logging.info('***TP3***: Emptying queue and closing connection.')
        while not self.__eventQueue.empty():
            qs = self.__eventQueue.qsize()
            if qs % 100 == 0:
                logging.info(f'***TP3***: Approximate points left: {qs}')
            event_list = self.__eventQueue.get()
            unique, counts = numpy.unique(event_list, return_counts=True)
            counts = counts.astype(numpy.uint32)
            self.__spimData[unique] += counts
        logging.info('***TP3***: SPIM finished.')

    def get_total_counts_from_data(self, frame_int):
        return numpy.sum(frame_int)

    def get_current(self, frame_int, frame_number):
        if self.__isCumul and frame_number:
            eps = (numpy.sum(frame_int) / self.__expTime) / frame_number
        else:
            eps = numpy.sum(frame_int) / self.__expTime
        cur_pa = eps / (6.242 * 1e18) * 1e12
        return cur_pa

    def create_image_from_bytes(self, frame_data, bitDepth, width, height):
        """
        Creates an image int8 (1 byte) from byte frame_data. If softBinning is True, we sum in Y axis.
        """
        frame_data = numpy.array(frame_data[:-1])
        if bitDepth == 8:
            dt = numpy.dtype(numpy.uint8).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        elif bitDepth == 16:
            dt = numpy.dtype(numpy.uint16).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        elif bitDepth == 32:
            dt = numpy.dtype(numpy.uint32).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        frame_int = numpy.reshape(frame_int, (height, width))
        # if self.__softBinning:
        #    frame_int = numpy.sum(frame_int, axis=0)
        #    frame_int = numpy.reshape(frame_int, (1, 1024))
        return frame_int

    def create_spimimage_from_bytes(self, frame_data, bitDepth, width, height, xspim, yspim):
        """
        Creates an image int8 (1 byte) from byte frame_data. No softBinning for now.
        """
        assert height == 1
        frame_data = numpy.array(frame_data[:-1])
        if bitDepth == 8:
            dt = numpy.dtype(numpy.uint8).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        if bitDepth == 16:
            dt = numpy.dtype(numpy.uint16).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        elif bitDepth == 32:
            dt = numpy.dtype(numpy.uint32).newbyteorder('>')
            frame_int = numpy.frombuffer(frame_data, dtype=dt)
            frame_int = frame_int.astype(numpy.float32)
        frame_int = numpy.reshape(frame_int, (self.__yspim, self.__xspim, width))
        return frame_int

    def create_spimimage_from_events(self):
        return self.__spimData.reshape((self.__xspim, self.__yspim, 1025))
