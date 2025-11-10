from datetime import datetime
from pathlib import Path
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model.container.base import BaseContainer


try:
    from win32api import GetLogicalDriveStrings
except ImportError:
    #prevent errors when importing module in non-windows environment
    pass

class RootContainer(BaseContainer):
    def __init__(self, sort_order, show_hidden: bool) -> None:
        Publisher.sendMessage('container.opened', container=self)
        BaseContainer.__init__(self, sort_order, show_hidden)

    def _list_paths(self) -> list[tuple[Path, datetime|None]]:
        return [(Path(str(path)), None) for path
                in GetLogicalDriveStrings().split('\x00')[:-1]]

    @property
    def name(self):
        #TODO: (3,3) Fix: Read name from win api
        return _('My Computer')
    
    @property
    def path(self) -> Path:
        return Path('/')
       
    def open_parent(self) -> BaseContainer:
        return self
    
    def can_delete_contents(self) -> bool:
        return False
    def can_delete_self(self) -> bool:
        return False
    
    @property
    def universal_path(self) -> Path|None:
        return None
