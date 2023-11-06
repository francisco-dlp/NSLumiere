import os, logging, json, sys

class FileManager:
    def __init__(self, filename):
        self.filename = filename
        if sys.platform.startswith('win'):
            abs_path = os.path.abspath('C:\\ProgramData\\Microscope\\' + filename + '.json')
        else:
            abs_path = os.path.abspath('/srv/data/' + filename + '.json')
        try:
            with open(abs_path) as savfile:
                self.abs_path = abs_path
                settings = json.load(savfile)
                self.settings = settings
        except FileNotFoundError:
            abs_path = os.path.join(os.path.dirname(__file__), filename + '.json')
            self.abs_path = abs_path
            with open(abs_path) as savfile:
                settings = json.load(savfile)
                self.settings = settings
        logging.info(f'***READ DATA***: Data type of {self.filename} found at {self.abs_path}.')

    def save_locally(self):
        abs_path = os.path.abspath('C:\\ProgramData\\Microscope\\' + self.filename + '.json')
        with open(abs_path, 'w+') as json_file:
            json.dump(self.settings, json_file, indent=4)

    def save_clone(self, new_path):
        abs_path = os.path.abspath('C:\\ProgramData\\Microscope\\' + new_path + '.json')
        with open(abs_path, 'w+') as json_file:
            json.dump(self.settings, json_file, indent=4)