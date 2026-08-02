from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.canvas import Canvas
from quivilib.model.favorites import Favorites
from quivilib.model.settings import Settings


class App(object):
    def __init__(self, conf, start_dir):
        self.settings: Settings = conf
        sort_order = conf.getint('FileList', 'SortOrder')
        #Must be created before container in order to notify if it's a favorite
        self.favorites = Favorites(conf)
        self.container = DirectoryContainer(start_dir, sort_order, False)
