import os
from configparser import RawConfigParser
from pubsub import pub as Publisher
from quivilib.model.container import SortOrder
from quivilib.model.commandenum import CommandName, FitSettings


class Settings(RawConfigParser):
    def __init__(self, path):
        RawConfigParser.__init__(self)
        self.path = path
        
        def _parseError():
            backupname = None
            if os.path.isfile(path):
                backupname = f'{path}.bad'
                os.replace(path, backupname)
            Publisher.sendMessage('settings.corrupt', backupFilename=backupname)
        
        #Try reading the config twice; first as utf-8 and then as the default encoding.
        #The write will now always be UTF-8, but existing files will be system default.
        try:
            self.read(path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                self.read(path)
            except:
                _parseError()
        except:
            #Any other error should be treated as a parse error; the file is probably corrupt.
            _parseError()
        self.__defaults = self._load_defaults()
        Publisher.sendMessage('settings.changed', settings=self)
        
    def _load_defaults(self):
        defaults = (
          ('Options', 'FitType', FitSettings.FIT_WIDTH_OVERSIZE),
          ('Options', 'FitWidthCustomSize', 800),
          ('Options', 'StartDir', ''),
          ('Options', 'CustomBackground', 0),
          ('Options', 'CustomBackgroundColor', '0,0,0'),
          ('Options', 'RealFullscreen', 0),
          ('Options', 'AutoFullscreen', 1),
          ('Options', 'UseRightToLeft', 0),
          ('Options', 'DetectSpreads', 0),
          ('Options', 'HorizontalScrollAtBottom', 0),
          ('Options', 'PlaceholderDelete', 1),
          ('Options', 'PlaceholderSingle', 0),
          ('Options', 'PlaceholderAutoOpen', 1),
          ('Options', 'OpenFirst', 0),
          ('Window', 'Perspective', ''),
          ('Window', 'MainWindowX', 50),
          ('Window', 'MainWindowY', 50),
          ('Window', 'MainWindowWidth', 700),
          ('Window', 'MainWindowHeight', 500),
          ('Window', 'MainWindowMaximized', '0'),
          ('Window', 'MainWindowFullscreen', '0'),
          ('Window', 'FileListColumnsWidth', ''),
          ('Mouse', 'LeftClickCmd', CommandName.DRAG_IMAGE),
          ('Mouse', 'MiddleClickCmd', CommandName.SELECT_NEXT),
          ('Mouse', 'RightClickCmd', CommandName.SHOW_FILE_LIST),
          ('Mouse', 'Aux1ClickCmd', -1),
          ('Mouse', 'Aux2ClickCmd', -1),
          ('Mouse', 'AlwaysLeftMouseDrag', 1),
          ('Mouse', 'DragThreshold', 0),
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
    
    def set(self, section: str, option: str, value: str|None = None):
        RawConfigParser.set(self, section, option, str(value))
        try:
            Publisher.sendMessage(f'settings.changed.{section}.{option}', settings=self)
        except Publisher.TopicNameError:
            #Avoid TopicNameError error (option can be a number, and
            #pubsub only accepts names starting with a letter)
            pass
    
    def save(self):
        if not self.path.parent.exists():
            self.path.parent.makedirs()
        with self.path.open('w', encoding='utf-8') as f:
            self.write(f)
            
    def get_default(self, section, option):
        for isection, ioption, ivalue in self.__defaults:
            if isection == section and ioption == option:
                return ivalue
        raise RuntimeError(f'Option {option} has no default value')
