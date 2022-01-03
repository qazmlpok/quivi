from __future__ import with_statement, absolute_import

from quivilib.gui.hotkeyctrl import GetAcceleratorName



class Shortcut(object):
    def __init__(self, flags, key_code):
        self.flags = flags
        self.key_code = key_code
        
    @property
    def name(self):
        return GetAcceleratorName((self.flags, self.key_code))

    def __eq__(self, other):
        return other and self.flags == other.flags and self.key_code == other.key_code
    
    def __ne__(self, other):
        return not self == other