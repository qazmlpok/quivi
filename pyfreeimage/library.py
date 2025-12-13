import ctypes
import sys
import os
import logging

from pyfreeimage.funct_list import FUNCTION_LIST
log = logging.getLogger('pyfreeimage.library')

lib = None

def load(file = None):
    global lib
    if not lib:
        lib = Library(file)
    return lib
    

class Library(object):
    def __init__(self, file):
        if not file:
            if sys.platform == 'win32':
                with os.add_dll_directory(os.getcwd()):
                    self.lib = ctypes.windll.freeimage
            else:
                self.lib = ctypes.cdll.LoadLibrary('libfreeimage.so.3')
                
        for function_descr in FUNCTION_LIST:
            try:
                self._bind(function_descr)
            except AttributeError:
                raise
        
        for name, pos in (('Load', 1), ('Save', 2), ('GetFileType', 0),
                          ('GetFIFFromFilename', 0)):
            if hasattr(self, name) and hasattr(self, name + 'U'):
                self._unicode_wrap(name, pos)
                
        #Enable the message output
        prototype = ctypes.CFUNCTYPE(None, ctypes.c_long, ctypes.c_char_p)
        self._callback_ref = prototype(self._error_handler)
        #SetOutputMessage uses C call; SetOutputMessageStdCall uses stdcall
        self.SetOutputMessage(self._callback_ref)
        self.last_error = ''
    
    def _unicode_wrap(self, name, pos):
        original_fn = getattr(self, name)
        unicode_fn = getattr(self, name + 'U')
        def unicode_detector_wrapper(*args):
            if isinstance(args[pos], bytes):
                return original_fn(*args)
            else:
                if 'linux' in sys.platform:
                    args = list(args)
                    args[pos] = args[pos].encode('utf-8')
                    return original_fn(*args)
                return unicode_fn(*args)
        setattr(self, name, unicode_detector_wrapper)
        setattr(self, name + 'A', unicode_fn)
        setattr(self, name + 'U', unicode_fn)
    
    def _bind(self, function_descr):
        restype = None
        name, add = function_descr[0:2]
        if len(function_descr) == 4:
            restype = function_descr[3]
        
        name_to_bind = name.split('_', 1)[1]
        
        function = getattr(self.lib, name)
        setattr(self, name_to_bind, function)
        
        if restype:
            function.restype = restype
    
    def _error_handler(self, fif, message) -> None:
        self.last_error = message
        log.error(message)
        
    def reset_last_error(self) -> None:
        self.last_error = ''
        
    def get_readable_fifs(self):
        return [i for i in range(1, self.GetFIFCount()) if self.FIFSupportsReading(i)]
    
    def get_fif_extensions(self, fif) -> list[str]:
        #GetFIFExtensionList returns bytes now, which needs to be turned into a string.
        #Everything returned by this should be in latin-1...
        resp: str = self.GetFIFExtensionList(fif).decode('latin-1')
        return ['.' + ext.casefold() for ext in resp.split(',')]
    
    def get_readable_extensions(self) -> list[str]:
        lst = []
        for fif in self.get_readable_fifs():
            lst += self.get_fif_extensions(fif)
        return lst
    
    def get_fif_description(self, fif) -> str:
        return self.GetFIFDescription(fif)
    
    def get_readable_extensions_descriptions(self) -> dict[str, str]:
        dic = {}
        for fif in self.get_readable_fifs():
            for ext in self.get_fif_extensions(fif):
                dic[ext] = self.get_fif_description(fif)
        return dic
