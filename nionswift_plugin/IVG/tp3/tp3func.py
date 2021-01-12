import json
import requests
import threading
import logging
import queue
import socket
import numpy

def SENDMYMESSAGEFUNC(sendmessagefunc):
    return sendmessagefunc

class TimePix3():
    def __init__(self, url, message):

        self.__serverURL = url
        self.__dataQueue = queue.LifoQueue()
        self.__isPlaying = False
        self.__softBinning = False
        self.sendmessage = message

        try:
            initial_status_code = self.status_code()
            if initial_status_code == 200:
                logging.info('***TP3***: Timepix has initialized correctly.')
            else:
                logging.info('***TP3***: Problem initializing Timepix')

        # Loading bpc and dacs
            bpcFile = '/home/asi/load_files/tpx3-demo.bpc'
            dacsFile = '/home/asi/load_files/tpx3-demo.dacs'
            self.cam_init(bpcFile, dacsFile)
        except:
            logging.info('***TP3***: Problem initializing Timepix')


    def status_code(self):
        try:
            resp = requests.get(url=self.__serverURL)
        except requests.exceptions.RequestException as e:  # Exceptions handling example
            return -1
        status_code = resp.status_code
        return status_code

    def dashboard(self):
        resp = requests.get(url=self.__serverURL + '/dashboard')
        data = resp.text
        dashboard = json.loads(data)
        return dashboard

    def cam_init(self, bpc_file, dacs_file):
        resp = requests.get(url=self.__serverURL + '/config/load?format=pixelconfig&file=' + bpc_file)
        data = resp.text
        logging.info(f'***TP3***: Response of loading binary pixel configuration file: ' + data)

        resp = requests.get(url=self.__serverURL + '/config/load?format=dacs&file=' + dacs_file)
        data = resp.text
        logging.info(f'***TP3***: Response of loading dacs file: ' + data)


    def get_config(self):
        resp = requests.get(url=self.__serverURL + '/detector/config')
        data = resp.text
        detectorConfig = json.loads(data)
        return detectorConfig

    def acq_init(self, detector_config, ntrig=99, shutter_open_ms=50):
        detector_config["nTriggers"] = ntrig
        detector_config["TriggerMode"] = "CONTINUOUS"
        detector_config["ExposureTime"] = shutter_open_ms / 1000

        resp = requests.put(url=self.__serverURL + '/detector/config', data=json.dumps(detector_config))
        data = resp.text
        # logging.info('Response of updating Detector Configuration: ' + data)


    def set_destination(self, port=0):
        options = ['count', 'tot', 'toa', 'tof']
        destination = {
             #"Raw": [{
             #   "Base": 'tcp://localhost:8090',
             #}],
            "Image": [{
                "Base": "tcp://localhost:8088",
                "Format": "jsonimage",
                "Mode": options[port]
            },
            {
                "Base": "tcp://localhost:8089",
                "Format": "jsonimage",
                "Mode": options[port],
                "IntegrationSize": -1,
                "IntegrationMode": "Sum"
            }
        ]
        }

        resp = requests.put(url=self.__serverURL + '/server/destination', data=json.dumps(destination))
        data = resp.text
        logging.info('***TP3***: Response of uploading the Destination Configuration to SERVAL : ' + data)
        logging.info(f'***TP3***: Selected port is {port} and corresponds to: ' + options[port])

    def getPortNames(self):
        return ['Counts', 'Time over Threshold (ToT)', 'Time of Arrival (ToA)', 'Time of Flight (ToF)']

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
        False

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
        pass

    def pauseSpim(self):
        pass

    def resumeSpim(self, mode):
        pass

    def stopSpim(self, immediate):
        return True

    def isCameraThere(self):
        return True

    def getTemperature(self):
        pass

    def setTemperature(self, temperature):
        pass

    def setupBinning(self):
        pass

    def startFocus(self, exposure, displaymode, accumulate):
        self.__softBinning = True if displaymode=='1d' else False
        port=8089 if accumulate else 8088
        if self.getCCDStatus() == "DA_RECORDING":
            self.stopFocus()
        if self.getCCDStatus() == "DA_IDLE":
            resp = requests.get(url=self.__serverURL + '/measurement/start')
            data = resp.text
            self.start_listening(port)
            return True

    def stopFocus(self):
        status = self.getCCDStatus()
        resp = requests.get(url=self.__serverURL + '/measurement/stop')
        data = resp.text
        self.finish_listening()

    def setExposureTime(self, exposure):
        detector_config = self.get_config()
        detector_config["ExposureTime"] = exposure
        resp = requests.put(url=self.__serverURL + '/detector/config', data=json.dumps(detector_config))
        data = resp.text

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
        pass

    def getGainName(self, cameraport, gain):
        pass

    def setGain(self, gain):
        pass

    def getReadoutTime(self):
        pass

    def getNumofPorts(self):
        pass

    def getPortName(self, portnb):
        pass

    def getCurrentPort(self):
        pass

    def setCurrentPort(self, cameraport):
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
        dashboard = json.loads(requests.get(url=self.__serverURL + '/dashboard').text)
        return dashboard["Measurement"]["Status"]

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
        pass

    def setArea(self, area: tuple):
        pass

    def getArea(self):
        return (0, 0, 2048, 2048)

    def setVideoThreshold(self, threshold):
        pass

    def getVideoThreshold(self):
        pass

    def setCCDOverscan(self, sx, sy):
        pass

    #Function of the client listener

    def start_listening(self, port=8088):
        self.__isPlaying = True
        self.__clientThread = threading.Thread(target=self.acquire_single_frame, args=(port,))
        self.__clientThread.start()

    def finish_listening(self):
        if self.__isPlaying:
            self.__isPlaying = False
            self.__clientThread.join()
            logging.info(f'***TP3***: Stopping acquisition. There was {self.__dataQueue.qsize()} items in the Queue.')
            self.__dataQueue = queue.LifoQueue()

    def acquire_single_frame(self, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        ip = socket.gethostbyname('129.175.108.52')
        address = (ip, port)
        try:
            client.connect(address)
            logging.info(f'***TP3***: Client connected.')
            client.settimeout(0.005)
        except ConnectionRefusedError:
            return False

        cam_properties = dict()
        frame_data = b''
        buffer_size = 1024
        frame_number = 0
        frame_time = 0

        def check_string_value(header, prop):
            start_index = header.index(prop)
            end_index = start_index + len(prop)
            begin_value = header.index(':', end_index, len(header)) + 1
            if prop == 'height':
                end_value = header.index('}', end_index, len(header))
            else:
                end_value = header.index(',', end_index, len(header))
            try:
                value = float(header[begin_value:end_value])
            except ValueError:
                value = str(header[begin_value:end_value])
            return value

        def put_queue(cam_prop, frame):
            self.__dataQueue.put((cam_prop, frame))

        while self.__isPlaying:
            '''
            Notes
            -----
            Loop based on self.__is_playing. 
            if b'timeAtFrame' is in data, header is there. A few unlikely issues will kill a tiny percentage of
            frames. They are basically headers chopped with a part in one chunk data (4096 bytes) to other chunk
            data. 
    
            I get both the beginning and the end of header. Most of data are:
                b'{HEADER}\n\x00\x00... ...\x00\n'
            This means initial frame_data is everything after header. So the beginning of a frame_data is simply
            data[end_header+2:].
    
            In some cases, however, you have a data like this:
                b'\x00\x00\x00{HEADER}\n\x00\x00... ...\x00\n'
            This means everything before HEADER actually is part of an previous imcomplete frame. This is handled
            in begin_header!=0. In this case, your new frame will always be data[end_header+2:]. I handle good frames
            using create_last_image, which creates this shared memory variable self.__lastImage and also sets the
            event thread to True so image can advance.
            '''
            try:
                data = client.recv(buffer_size)
                if len(data) <= 0:
                    logging.info('***TP3***: Received null bytes')
                elif b'{' in data:
                    data += client.recv(1024)
                    begin_header = data.index(b'{')
                    end_header = data.index(b'}')
                    header = data[begin_header:end_header + 1].decode()
                    for properties in ['timeAtFrame', 'frameNumber', 'measurementID', 'dataSize', 'bitDepth', 'width',
                                       'height']:
                        cam_properties[properties] = (check_string_value(header, properties))
                    buffer_size = int(cam_properties['dataSize'] / 4.)
                    frame_number = int(cam_properties['frameNumber'])
                    frame_time = int(cam_properties['timeAtFrame'])
                    if begin_header != 0:
                        frame_data += data[:begin_header]
                        if len(frame_data) == cam_properties['dataSize'] + 1: put_queue(cam_properties, frame_data)
                    frame_data = data[end_header + 2:]
                else:
                    try:
                        frame_data += data
                    except Exception as e:
                        logging.info(f'Exception is {e}')
                    if len(frame_data) == cam_properties['dataSize'] + 1: put_queue(cam_properties, frame_data)
            except socket.timeout:
                pass
                if not self.__dataQueue.empty(): self.sendmessage(1)
        logging.info(f'***TP3***: Number of counted frames is {frame_number}. Last frame arrived at {frame_time}.')
        return True

    def get_last_data(self):
        return self.__dataQueue.get()

    def create_image_from_bytes(self, frame_data):
        frame_data = numpy.array(frame_data[:-1])
        frame_int = numpy.frombuffer(frame_data, dtype=numpy.int8)
        frame_int = numpy.reshape(frame_int, (256, 1024))
        if self.__softBinning:
            frame_int = numpy.sum(frame_int, axis=0)
            frame_int = numpy.reshape(frame_int, (1, 1024))
        return frame_int
