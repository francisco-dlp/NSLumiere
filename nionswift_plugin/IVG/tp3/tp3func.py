import json
import requests
import threading
import logging
import time

class TimePix3():
    def __init__(self, url):

        self.__serverURL = url
        self.__thread = None
        self.__dataEvent = threading.Event()

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


    def set_destination(self):
        destination = {
             #"Raw": [{
                # URI to a folder where to place the raw files.
                # "Base": pathlib.Path(os.path.join(os.getcwd(), 'data')).as_uri(),
             #   "Base": 'tcp://localhost:8089',
                # How to name the files for the various frames.
                #"FilePattern": "raw%Hms_",
             #}],
            "Image": [{
                "Base": "tcp://localhost:8088",
                "Format": "jsonimage",
                "Mode": "count"
            }]
        }
        resp = requests.put(url=self.__serverURL + '/server/destination', data=json.dumps(destination))
        data = resp.text
        # logging.info('Response of uploading the Destination Configuration to SERVAL : ' + data)


    def acq_single(self):
        self.__thread = threading.Thread(target=self._acq_simple, args=(),)
        self.__thread.start()

    def acq_wait(self):
        self.__thread.join()

    def detector_status(self):
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


    def acq_alive(self):
        return self.__thread.is_alive()

    def _acq_simple(self):
        start=time.time()
        if self.detector_status() == "DA_IDLE":
            resp = requests.get(url=self.__serverURL + '/measurement/start')
            data = resp.text
            #logging.info('Response of acquisition start: ' + data)
            taking_data = True
            while taking_data:
                dashboard = json.loads(requests.get(url=self.__serverURL + '/dashboard').text)
                #logging.info(dashboard)
                time.sleep(0.01)
                status = self.detector_status()
                if status == "DA_STOPPING":
                    print('data dispo')
                    print(time.time() - start)
                if status == "DA_IDLE":
                    taking_data = False
                    resp = requests.get(url=self.__serverURL + '/measurement/stop')
                    data = resp.text
                    #logging.info('Acquisition was stopped with response: ' + data)

    def start_acq_simple(self):
        if self.detector_status() == "DA_IDLE":
            resp = requests.get(url=self.__serverURL + '/measurement/start')
            data = resp.text
            #logging.info('Response of acquisition start: ' + data)
            #while True:
            #    dashboard = json.loads(requests.get(url=self.__serverURL + '/dashboard').text)
            #    #logging.info(dashboard)
            #    time.sleep(0.005)
            #    if self.detector_status() == "DA_STOPPING": break

    def finish_acq_simple(self):
        status = self.detector_status()
        resp = requests.get(url=self.__serverURL + '/measurement/stop')
        data = resp.text
        # logging.info('Acquisition was stopped with response: ' + data)

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
        return (256, 1024)

    def registerLogger(self, fn):
        pass

    def addConnectionListener(self, fn):
        pass

    @property
    def simulation_mode(self) -> bool:
        pass

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
        pass

    def stopFocus(self):
        return True

    def setExposureTime(self, exposure):
        pass

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
        return res

    def getReadoutTime(self):
        pass

    def getNumofPorts(self):
        pass

    def getPortName(self, portnb):
        pass

    def getCurrentPort(self):
        pass

    def setCurrentPort(self, cameraport):
        pass

    def getMultiplication(self):
        pass

    def setMultiplication(self, multiplication):
        pass

    def getCCDStatus(self) -> dict():
        pass

    def getReadoutSpeed(self):
        pass

    def getPixelTime(self, cameraport, speed):
        pass

    def adjustOverscan(self, sizex, sizey):
        pass

    def setTurboMode(self, active, sizex, sizey):
        pass

    def getTurboMode(self):
        pass

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
        pass

    def setVideoThreshold(self, threshold):
        pass

    def getVideoThreshold(self):
        pass

    def setCCDOverscan(self, sx, sy):
        pass
