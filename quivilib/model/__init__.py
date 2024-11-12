from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.canvas import Canvas
from quivilib.model.favorites import Favorites


class App(object):
    def __init__(self, settings, start_dir):
        self.settings = settings
        sort_order = settings.getint('FileList', 'SortOrder')
        #Must be created before container in order to notify if it's a favorite
        self.favorites = Favorites(settings)
        self.container = DirectoryContainer(start_dir, sort_order, False)
