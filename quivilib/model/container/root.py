

from quivilib.i18n import _
from quivilib.model.container import Item
from quivilib.model.container.base import BaseContainer
from pathlib import Path

from wx.lib.pubsub import pub as Publisher

try:
    from win32api import GetLogicalDriveStrings
except ImportError:
    #prevent errors when importing module in non-windows environment
    pass

class RootContainer(BaseContainer):
    def __init__(self, sort_order, show_hidden):
        Publisher.sendMessage('container.opened', self)
        BaseContainer.__init__(self, sort_order, show_hidden)
                
    def _list_paths(self):
        return [(Path(str(path)), None, None) for path
                in GetLogicalDriveStrings().split('\x00')[:-1]]

    @property
    def name(self):
        #TODO: (3,3) Fix: Read name from win api
        return _('My Computer')
    
    @property
    def path(self):
        return ''
       
    def open_parent(self):
        return None
    
    def can_delete(self):
        return False
    
    @property
    def universal_path(self):
        return None

