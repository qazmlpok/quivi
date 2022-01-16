

from quivilib.model.container import SortOrder

from configparser import SafeConfigParser

from pubsub import pub as Publisher



class UnicodeAwareConfigParser(SafeConfigParser):
    def set(self, section, option, value):
        value = str(value).encode('utf-8')
        SafeConfigParser.set(self, section, option, value)

    def get(self, section, option):
        value = SafeConfigParser.get(self, section, option)
        return value.decode('utf-8')
    
    def items(self, section):
        options = self.options(section)
        return [(option, self.get(section, option)) for option in options]
    
    
#I don't believe UnicodeAwareConfigParser is necessary in python3.
#(If it is, remember to add kwargs to the wrapper functions)
class Settings(SafeConfigParser):
    (FIT_NONE,
     FIT_WIDTH_OVERSIZE,
     FIT_HEIGHT_OVERSIZE,
     FIT_BOTH_OVERSIZE,
     FIT_CUSTOM_WIDTH,
     FIT_SCREEN_CROP_EXCESS,
     FIT_SCREEN_SHOW_ALL,
     FIT_SCREEN_NONE,
     FIT_TILED,
     FIT_WIDTH,
     FIT_HEIGHT,
     FIT_BOTH) = list(range(12))
     
    (ZOOM_DEFAULT,
     ZOOM_SYSTEM,
     ZOOM_NEIGHBOR,
     ZOOM_BILINEAR,
     ZOOM_BICUBIC,
     ZOOM_CATMULLROM) = list(range(6))
     
    (MOVE_DRAG,
     MOVE_LOCK) = list(range(2))
    
    (BG_SYSTEM,
     BG_BLACK,
     BG_WHITE) = list(range(3))
    
    def __init__(self, path):
        SafeConfigParser.__init__(self)
        self.path = path
        self.read(path)
        self.__defaults = self._load_defaults()
        Publisher.sendMessage('settings.changed', settings=self)
        
    def _load_defaults(self):
        defaults = (
          ('Options', 'FitType', self.FIT_WIDTH_OVERSIZE),
          ('Options', 'FitWidthCustomSize', 800),
          ('Options', 'StartDir', ''),
          ('Options', 'CustomBackground', 0),
          ('Options', 'CustomBackgroundColor', '0,0,0'),
          ('Options', 'RealFullscreen', 0),
          ('Options', 'OpenFirst', 0),
          ('Window', 'Perspective', ''),
          ('Window', 'MainWindowX', 50),
          ('Window', 'MainWindowY', 50),
          ('Window', 'MainWindowWidth', 700),
          ('Window', 'MainWindowHeight', 500),
          ('Window', 'MainWindowMaximized', '0'),
          ('Window', 'FileListColumnsWidth', ''),
          #TODO: (2,2) Refactor: change to constant. This is a dummy command ID
          # for "drag image"
          ('Mouse', 'LeftClickCmd', -1),
          ('Mouse', 'MiddleClickCmd', 12001),
          ('Mouse', 'RightClickCmd', 13007),
          ('FileList', 'SortOrder', SortOrder.TYPE),
          ('Language', 'ID', 'default'),
          ('Update', 'LastCheck', ''),
          ('Update', 'Available', '0'),
          ('Update', 'URL', ''),
          ('Update', 'Version', ''),
        )
        for section, option, value in defaults:
            if not self.has_section(section):
                self.add_section(section)
            if not self.has_option(section, option):
                self.set(section, option, value)
        return defaults
    
    def set(self, section, option, value):
        SafeConfigParser.set(self, section, option, value)
        try:
            Publisher.sendMessage('settings.changed.%s.%s' % (section, option), settings=self)
        except Publisher.TopicNameError:
            #Avoid TopicNameError error (option can be a number, and
            #pubsub only accepts names starting with a letter)
            pass
    
    def save(self):
        if not self.path.parent.exists():
            self.path.parent.makedirs()
        with self.path.open('w') as f:
            self.write(f)
            
    def get_default(self, section, option):
        for isection, ioption, ivalue in self.__defaults:
            if isection == section and ioption == option:
                return ivalue
        raise RuntimeError('Option %s has no default value' % option)
        