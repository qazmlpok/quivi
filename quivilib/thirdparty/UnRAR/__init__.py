from __future__ import generators

# Copyright (c) 2003-2005 Jimmy Retzlaff
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# This version was modified by Conrado Porto Lopes Gouvea
# in order to fix a race condition when opening 0 byte files
# and a reference cycle that would prevent Archive's being garbage collected
# which would prevent the opening of RAR files after several of them were
# open.

"""
pyUnRAR is a ctypes based wrapper around the free UnRAR.dll. It
enables reading and unpacking of archives created with the
RAR/WinRAR archivers. There is a low-level interface which is very
similar to the C interface provided by UnRAR. There is also a
higher level interface which makes some common operations easier.
"""

__version__ = '1.1'


import fnmatch
import os
import Queue
import threading
import time

import ctypes.wintypes

# Low level interface - see UnRARDLL\UNRARDLL.TXT

ERAR_END_ARCHIVE = 10
ERAR_NO_MEMORY = 11
ERAR_BAD_DATA = 12
ERAR_BAD_ARCHIVE = 13
ERAR_UNKNOWN_FORMAT = 14
ERAR_EOPEN = 15
ERAR_ECREATE = 16
ERAR_ECLOSE = 17
ERAR_EREAD = 18
ERAR_EWRITE = 19
ERAR_SMALL_BUF = 20
ERAR_UNKNOWN = 21

RAR_OM_LIST = 0
RAR_OM_EXTRACT = 1

RAR_SKIP = 0
RAR_TEST = 1
RAR_EXTRACT = 2

RAR_VOL_ASK = 0
RAR_VOL_NOTIFY = 1

RAR_DLL_VERSION = 3

# enum UNRARCALLBACK_MESSAGES
UCM_CHANGEVOLUME = 0
UCM_PROCESSDATA = 1
UCM_NEEDPASSWORD = 2


unrar = ctypes.WinDLL('unrar.dll')

class RAROpenArchiveData(ctypes.Structure):
    def __init__(self, ArcName=None, OpenMode=RAR_OM_LIST):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, ArcName=ArcName, OpenMode=OpenMode, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char_p),
                ('OpenMode', ctypes.c_uint),
                ('OpenResult', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
               ]

class RAROpenArchiveDataEx(ctypes.Structure):
    def __init__(self, ArcName=None, ArcNameW=u'', OpenMode=RAR_OM_LIST):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, ArcName=ArcName, ArcNameW=ArcNameW, OpenMode=OpenMode, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char_p),
                ('ArcNameW', ctypes.c_wchar_p),
                ('OpenMode', ctypes.c_uint),
                ('OpenResult', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
                ('Flags', ctypes.c_uint),
                ('Reserved', ctypes.c_uint*32),
               ]

class RARHeaderData(ctypes.Structure):
    def __init__(self):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char*260),
                ('FileName', ctypes.c_char*260),
                ('Flags', ctypes.c_uint),
                ('PackSize', ctypes.c_uint),
                ('UnpSize', ctypes.c_uint),
                ('HostOS', ctypes.c_uint),
                ('FileCRC', ctypes.c_uint),
                ('FileTime', ctypes.c_uint),
                ('UnpVer', ctypes.c_uint),
                ('Method', ctypes.c_uint),
                ('FileAttr', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
               ]

class RARHeaderDataEx(ctypes.Structure):
    def __init__(self):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char*1024),
                ('ArcNameW', ctypes.c_wchar*1024),
                ('FileName', ctypes.c_char*1024),
                ('FileNameW', ctypes.c_wchar*1024),
                ('Flags', ctypes.c_uint),
                ('PackSize', ctypes.c_uint),
                ('PackSizeHigh', ctypes.c_uint),
                ('UnpSize', ctypes.c_uint),
                ('UnpSizeHigh', ctypes.c_uint),
                ('HostOS', ctypes.c_uint),
                ('FileCRC', ctypes.c_uint),
                ('FileTime', ctypes.c_uint),
                ('UnpVer', ctypes.c_uint),
                ('Method', ctypes.c_uint),
                ('FileAttr', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
                ('Reserved', ctypes.c_uint*1024),
               ]

def DosDateTimeToTimeTuple(dosDateTime):
    """Convert an MS-DOS format date time to a Python time tuple.
    """
    dosDate = dosDateTime >> 16
    dosTime = dosDateTime & 0xffff
    day = dosDate & 0x1f
    month = (dosDate >> 5) & 0xf
    year = 1980 + (dosDate >> 9)
    second = 2*(dosTime & 0x1f)
    minute = (dosTime >> 5) & 0x3f
    hour = dosTime >> 11
    return time.localtime(time.mktime((year, month, day, hour, minute, second, 0, 1, -1)))

def _wrap(restype, function, argtypes):
    result = function
    result.argtypes = argtypes
    result.restype = restype
    return result

RARGetDllVersion = _wrap(ctypes.c_int, unrar.RARGetDllVersion, [])

RAROpenArchive = _wrap(ctypes.wintypes.HANDLE, unrar.RAROpenArchive, [ctypes.POINTER(RAROpenArchiveData)])
RAROpenArchiveEx = _wrap(ctypes.wintypes.HANDLE, unrar.RAROpenArchiveEx, [ctypes.POINTER(RAROpenArchiveDataEx)])

RARReadHeader = _wrap(ctypes.c_int, unrar.RARReadHeader, [ctypes.wintypes.HANDLE, ctypes.POINTER(RARHeaderData)])
RARReadHeaderEx = _wrap(ctypes.c_int, unrar.RARReadHeaderEx, [ctypes.wintypes.HANDLE, ctypes.POINTER(RARHeaderDataEx)])

_RARSetPassword = _wrap(ctypes.c_int, unrar.RARSetPassword, [ctypes.wintypes.HANDLE, ctypes.c_char_p])
def RARSetPassword(*args, **kwargs):
    _RARSetPassword(*args, **kwargs)

RARProcessFile = _wrap(ctypes.c_int, unrar.RARProcessFile, [ctypes.wintypes.HANDLE, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p])

RARCloseArchive = _wrap(ctypes.c_int, unrar.RARCloseArchive, [ctypes.wintypes.HANDLE])

UNRARCALLBACK = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint, ctypes.c_long, ctypes.c_long, ctypes.c_long)
_RARSetCallback = _wrap(None, unrar.RARSetCallback, [ctypes.wintypes.HANDLE, UNRARCALLBACK, ctypes.c_long])
def RARSetCallback(*args, **kwargs):
    _RARSetCallback(*args, **kwargs)


# Higher level interface

class ArchiveHeaderBroken(Exception): pass
class InvalidRARArchive(Exception): pass
class FileOpenError(Exception): pass

RARExceptions = {
                 ERAR_NO_MEMORY : MemoryError,
                 ERAR_BAD_DATA : ArchiveHeaderBroken,
                 ERAR_BAD_ARCHIVE : InvalidRARArchive,
                 ERAR_EOPEN : FileOpenError,
                }


class _FileLikeObject:
    """Implement a file like object accessible from RARFile."""

    def __init__(self, rarFile, mode):
        """Called by RARFile.open, do not call directly."""
        self.rarFile = rarFile
        self.mode = mode
        self.dataFromCallback = Queue.Queue()
        self.readBuffer = []
        self.readBufferLength = 0
        self.position = 0
        self.doneReading = False
        self.name = self.rarFile.filename
        self.lineQueue = Queue.Queue()

    def __iter__(self):
        while True:
            line = self.readline()
            if line:
                yield line
            else:
                break

    def close(self):
        """Emulate file(...).close()."""
        pass
    
    def flush(self):
        """Emulate file(...).flush()."""
        pass

    def read(self, size=-1):
        """Emulate file(...).read(...)."""
        if size < 0:
            size = self.rarFile.size

        if not self.doneReading:
            while not self.doneReading:
                self.readBuffer.append(self.dataFromCallback.get())
                if self.readBuffer[-1] is None:
                    self.doneReading = True
                    del self.readBuffer[-1]
                else:
                    self.readBufferLength += len(self.readBuffer[-1])

        result = ''.join(self.readBuffer)
        if len(result) <= size:
            self.readBuffer = []
            self.readBufferLength = 0
        else:
            self.readBuffer = [result[size:]]
            self.readBufferLength = len(self.readBuffer[0])
            result = result[:size]

        self.position += len(result)

        if self.mode == 't':
            result = result.replace('\r\n', '\n')

        # If threads remain open when Python shuts down them spurious
        # exceptions can result. So we automatically try to close the
        # file when appropriate (which ends the thread) in case the
        # user doesn't.
        if self.rarFile.size == self.position:
            self.close()

        return result

    def readline(self, size=-1):
        """Emulate file(...).readline(...)."""
        if self.lineQueue.qsize() < 2:
            buffer = self.read(256*1024)
            if buffer:
                if not self.lineQueue.empty():
                    buffer = self.lineQueue.get() + buffer
                buffer = buffer.split('\n')
                for line in buffer[:-1]:
                    self.lineQueue.put(line+'\n')
                if len(buffer) > 1:
                    if not buffer[-1]:
                        self.lineQueue.put(buffer[-1]+'\n')
                    else:
                        self.lineQueue.put(buffer[-1])

        if self.lineQueue.empty():
            result = ''
        else:
            result = self.lineQueue.get()

        return result

    def readlines(self, sizehint=-1):
        """Emulate file(...).readlines(...)."""
        if 0 < sizehint < self.rarFile.size:
            size = sizehint
        else:
            size = self.rarFile.size

        lines = []
        sizeRead = 0
        while True:
            lines.append(self.readline())
            sizeRead += len(lines[-1])
            if 0 < size <= sizeRead or not lines[-1]:
                break

        if not lines[-1]:
            del lines[-1]

        return lines

    def seek(self, offset, whence=0):
        """Emulate file(...).seek(...).

        Seeks cannot move backwards in the file. Seeking forward
        requires decompressing the file until the seek-point which
        can be time consuming.
        """
        position = offset
        if whence == 1:
            position += self.position
        elif whence == 2:
            position += self.rarFile.size

        assert position >= self.position
        self.read(position-self.position)

    def tell(self):
        """Emulate file(...).tell()."""
        return self.position

    def __callback(self, msg, UserData, P1, P2):
        if msg == UCM_PROCESSDATA:
            self.dataFromCallback.put((ctypes.c_char*P2).from_address(P1).raw)
        return 1

    def expansionThread(self):
        try:
            self.__callback_ref = UNRARCALLBACK(self.__callback)
            RARSetCallback(self.rarFile.RAR._handle, self.__callback_ref, 0)
            RARProcessFile(self.rarFile.RAR._handle, RAR_TEST, None, None)
        finally:
            self.dataFromCallback.put(None)


class RARFile:
    """Represent a file in an archive. Don't instantiate directly.

    Properties:
        filename - name of the file in the archive including path (if any)
        datetime - file date/time as a struct_time suitable for time.strftime
        isdir - True if the file is a directory
        size - size in bytes of the uncompressed file
        comment - comment associated with the file

    Note - this is not currently intended to be a Python file-like object.
    """

    def __init__(self, RAR, headerData):
        self.RAR = RAR
        self.filename = headerData.FileNameW
        self.datetime = DosDateTimeToTimeTuple(headerData.FileTime)
        self.isdir = ((headerData.Flags & 0xE0) == 0xE0)
        self.size = headerData.UnpSize + (headerData.UnpSizeHigh << 32)
        if headerData.CmtState == 1:
            self.comment = headerData.CmtBuf.value
        else:
            self.comment = None

        self._extracted = False

    def extract(self, filename=None):
        """Extract the file to the file system."""

        self._extracted = True
        RARProcessFile(self.RAR._handle, RAR_EXTRACT, None, filename)

    def open(self, mode='rb'):
        """Open a file-like object.

        Because of the style of the UnRAR.dll API for extracting files
        without writing to disk, extraction must be done in a background
        thread. This is encapsulated by pyUnRAR, but you should be aware
        that calling this method results in a thread being spawned.

        >>> for fileInArchive in Archive('test.rar').iterfiles():
        ...     if fileInArchive.filename.endswith('test.txt'):
        ...        print fileInArchive.open('rt').read()
        This is only a test.
        """

        assert mode[0] == 'r' and (len(mode) == 1 or (len(mode) ==2 and mode[1] in 'bt'))
        if 't' in mode:
            mode = 't'
        else:
            mode = 'b'

        self._extracted = True
        fileLikeObject = _FileLikeObject(self, mode)
        fileLikeObject.expansionThread()
        return fileLikeObject

    def __str__(self):
        return '<RARFile "%s" in "%s">' % (self.filename, self.RAR.archiveName)

    def _skip(self):
        if not self._extracted:
            RARProcessFile(self.RAR._handle, RAR_SKIP, None, None)


class Archive:
    """Open and operate on an archive."""

    def __init__(self, archiveName, password=None):
        """Instantiate the archive.

        archiveName is the name of the RAR file.
        password is used to decrypt the files in the archive.

        Properties:
            comment - comment associated with the archive

        >>> print Archive('test.rar').comment
        This is a test.
        """
        self.archiveName = archiveName
        archiveData = RAROpenArchiveDataEx(ArcNameW=self.archiveName, OpenMode=RAR_OM_EXTRACT)
        self._handle = RAROpenArchiveEx(ctypes.byref(archiveData))

        if archiveData.OpenResult != 0:
            raise RARExceptions[archiveData.OpenResult]

        if archiveData.CmtState == 1:
            self.comment = archiveData.CmtBuf.value
        else:
            self.comment = None

        if password:
            RARSetPassword(self._handle, password)

    def close(self):
        if self._handle and RARCloseArchive:
            RARCloseArchive(self._handle)

    def extract(self, filespec='*'):
        """Extract all files in the archive matching the filespec.

        >>> Archive('test.rar').extract('*.pyc')
        """
        for rarFile in self.iterfiles():
            if fnmatch.fnmatch(rarFile.filename, filespec):
                rarFile.extract()

    def iterfiles(self):
        """Iterate over all the files in the archive.

        The yielded RARFile should not be stored, it is not valid once
        the next iteration has occurred.

        >>> import os
        >>> for fileInArchive in Archive('test.rar').iterfiles():
        ...     print os.path.split(fileInArchive.filename)[-1],
        ...     print fileInArchive.isdir,
        ...     print fileInArchive.size,
        ...     print fileInArchive.comment,
        ...     print fileInArchive.datetime,
        ...     print time.strftime('%a, %d %b %Y %H:%M:%S', fileInArchive.datetime)
        test True 0 None (2003, 6, 30, 1, 59, 48, 0, 181, 1) Mon, 30 Jun 2003 01:59:48
        test.txt False 20 None (2003, 6, 30, 2, 1, 2, 0, 181, 1) Mon, 30 Jun 2003 02:01:02
        this.py False 1030 None (2002, 2, 8, 16, 47, 48, 4, 39, 0) Fri, 08 Feb 2002 16:47:48
        """
        headerData = RARHeaderDataEx()
        while not RARReadHeaderEx(self._handle, ctypes.byref(headerData)):
            rarFile = RARFile(self, headerData)
            yield rarFile
            rarFile._skip()
