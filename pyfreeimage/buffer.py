"""
"The contents of this file are subject to the FreeImage Public License
Version 1.0 (the "License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at
http://home.wxs.nl/~flvdberg/freeimage-license.txt

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
the specific language governing rights and limitations under the License. 
"""
import traceback
import ctypes as C
from constants import *

class IO(object):
    """Wrapped FreeImageIO structure used by the handle functions.
       Implement the callback functions as instance methods.
       
       Has the virtual methods ReadProc, WriteProc, SeekProc and TellProc.
       @author: Lenard Lindstrom
    """
    from sys import exc_info as _exc_info
    
    def __init__(self, fi):
        """
        """
        self.fi = fi
        self._as_structure = FreeImageIO(FI_ReadProc(self.__ReadProc),
                                         FI_WriteProc(self.__WriteProc),
                                         FI_SeekProc(self.__SeekProc),
                                         FI_TellProc(self.__TellProc))
        # Pre-alllocate error attributes in case of MemoryError
        self.iserror = False
        self._e = self._traceback = None

    def __ReadProc(self, buffer, size, count, handle):
        if not self.iserror:
            try:
                return self.ReadProc(buffer, size, count)
            except MemoryError, e:
                # Special case: avoid allocating more memory
                self._e = e
            except:
                #traceback.print_exc()
                etype, self._e, self._traceback = self._exc_info()
            self.iserror = True
        return 0    # Indicate error

    def __WriteProc(self, buffer, size, count, handle):
        if not self.iserror:
            try:
                return self.WriteProc(buffer, size, count)
            except MemoryError, e:
                # Special case: avoid allocating more memory
                self._e = e
            except:
                traceback.print_exc()
                etype, self._e, self._traceback = self._exc_info()
            self.iserror = True
        return 0    # Indicate error

    def __SeekProc(self, handle, offset, origin):
        if not self.iserror:
            try:
                return self.SeekProc(offset, origin)
            except MemoryError, e:
                # Special case: avoid allocating more memory
                self._e = e
            except:
                traceback.print_exc()
                etype, self._e, self._traceback = self._exc_info()
            self.iserror = True
        return 1    # Indicate error

    def __TellProc(self, handle):
        if not self.iserror:
            try:
                return self.TellProc()
            except MemoryError, e:
                # Special case: avoid allocating more memory
                self._e = e
            except:
                traceback.print_exc()
                etype, self._e, self._traceback = self._exc_info()
            self.iserror = True
        return -1    # Indicate error

    def ReadProc(self, buffer, size, count):
        """Dummy read proc. Indicate error."""
        return 0

    def WriteProc(self, buffer, size, count):
        """Dummy write proc. Indicate error."""
        return 0

    def SeekProc(self, offset, origin):
        """Dummy seek proc. Indicate error."""
        return 1

    def TellProc(self):
        """Dummy tell proc. Indicate error."""
        return -1

    def load(self, fif, flags=0):
        """
        Load an image from the source this instance represents.
        
        @param fif: FreeImage file type
        @type fif: int
        @return: bitmap
        @rtype: int
        """
        retval = self.fi.LoadFromHandle(fif, C.byref(self._as_structure), 1, flags)
        # Exception check is inlined in case of a MemoryError
        if self.iserror:
            try:
                raise self._e, None, self._traceback
            finally:
                # Avoid circular references through traceback
                self._traceback = self._e = None
                self.iserror = False
        return retval

    def save(self, fif, bitmap, flags=0):
        """
        Save an image to the destination this instance represents.
        
        @param fif: FreeImage file type
        @type fif: int
        @param bitmap: Bitmap
        @type bitmap: int
        
        @return: True if it's all ok
        @rtype: int
        
        """
        retval = self.fi.SaveToHandle(fif, bitmap, C.byref(self._as_structure), 1, flags)
        # Exception check is inlined in case of a MemoryError
        if self.iserror:
            try:
                raise self._e, None, self._traceback
            finally:
                # Avoid circular references through traceback
                self._traceback = self._e = None
                self.iserror = False
        return retval

    def getType(self):
        """ 
        GetFileType from handle
        
        @return: fif type
        @rtype: int
        """
        retval = self.fi.GetFileTypeFromHandle(C.byref(self._as_structure), 1, 0)
        # Exception check is inlined in case of a MemoryError
        if self.iserror:
            try:
                raise self._e, None, self._traceback
            finally:
                # Avoid circular references through traceback
                self._traceback = self._e = None
                self.iserror = False
        return retval

_PyString_FromStringAndSize = C.pythonapi.PyString_FromStringAndSize
_PyString_FromStringAndSize.argtypes = [BYTE_P, C.c_int]
_PyString_FromStringAndSize.restype = C.py_object

class FileIO(IO):
    """
    Wrapped python file object for use with the handle functions.
    @author: Lenard Lindstrom
    """
    def __init__(self, fi, f):
        """ 
        @param fi: FreeImagePy istance
        @type fi: Istance
        @param f: File object where load and save
        @type f: file
        """
        IO.__init__(self, fi)
        self._file = f

    def ReadProc(self, buffer, size, count):
        try:
            read = self._file.read
        except AttributeError:
            raise IOAttributeError, "Unsupported file operation read"
        line = read(size * count)
        n = len(line)
        C.memmove(buffer, line, n)
        count = n // size
        return count

    def WriteProc(self, buffer, size, count):
        try:
            write = self._file.write
        except AttributeError:
            raise IOAttributeError, "Unsupported file operation write"
        write(_PyString_FromStringAndSize(buffer, size * count))
        return count

    def SeekProc(self, offset, origin):
        try:
            seek = self._file.seek
        except AttributeError:
            raise IOAttributeError, "Unsupported file operation seek"
        seek(offset, origin)
        return 0

    def TellProc(self):
        try:
            tell = self._file.tell
        except AttributeError:
            raise IOAttributeError, "Unsupported file operation tell"
        pos = tell()
        return pos


