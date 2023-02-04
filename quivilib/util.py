

from pathlib import Path

import wx
import re
import sys
from functools import update_wrapper
import traceback
import locale
import string




def get_icon_for_extension(ext, small=True):
    if sys.platform == 'win32':
        from quivilib.windows.util import get_icon_for_extension as fn
        return fn(ext, small)
    size = (16, 16) if small else (32, 32)
    #TODO (3,?): Investigate: this gives 'not found' message boxes
    #Updated code for wx4; seems to work ok.
    icon = None
    #file_type = wx.TheMimeTypesManager.GetFileTypeFromExtension(ext[1:])
    #if file_type:
    #    icon = file_type.GetIcon()
    #    if not icon.IsOk():
    #        icon = None
    if not icon:
        icon = wx.ArtProvider.GetIcon(wx.ART_NORMAL_FILE, wx.ART_OTHER, size)
    return icon

def get_icon_for_directory(small=True):
    if sys.platform == 'win32':
        from quivilib.windows.util import get_icon_for_directory as fn
        return fn(small)
    size = (16, 16) if small else (32, 32)
    return wx.ArtProvider.GetIcon(wx.ART_FOLDER, wx.ART_OTHER, size)

def rescale_by_size_factor(width, height, max_width, max_height):
    assert width >= 0 and height >= 0 and max_height >= 0 and max_height >= 0
    if width == 0 or height == 0:
        return 1
    
    INFINITY = 0 #just for clarification
    img_wh = width / float(height)
    scr_wh = max_width / float(max_height) if max_height else INFINITY
    
    if max_width != INFINITY and (max_height == INFINITY or img_wh > scr_wh):
        return max_width / float(width)
    elif max_height != INFINITY and (max_width == INFINITY or img_wh <= scr_wh):
        return max_height / float(height)
    else:
        return 1


def error_handler(callback_fn):
    """Decorator that catches any exceptions and calls a callback function
    as callback_fn(exception, args, kwargs)
    """
    def error_handler_with_callback(fn):
        def error_handler_fn(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                callback_fn(e, args, kwargs)
        return update_wrapper(error_handler_fn, fn)
    return error_handler_with_callback


class ExceptionStr(object):
    def __init__(self, content):
        self.content = content
        self.infos = []
        
    def add_info(self, info):
        self.infos.insert(0, info)
        
    def __call__(self):
        return '\n'.join(self.infos + ['(' + self.content + ')']) 

def add_exception_info(exception, additional_info):
    str_fn = getattr(exception, "__str__", None)
    if not isinstance(str_fn, ExceptionStr):
        str_fn = ExceptionStr(str(exception))
        setattr(exception, 'get_custom_msg', str_fn)
    str_fn.add_info(additional_info)
    
def add_exception_custom_msg(exception, msg):
    def get_msg():
        return msg
    setattr(exception, 'get_custom_msg', get_msg)


def is_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return hasattr(sys, "frozen")

def get_exe_path():
    return Path(sys.executable).resolve()

def get_traceback():
    return traceback.format_exc()

def synchronized_method(lock_name):
    """ Synchronization decorator. """
    def decorator(f):
        def synchronized_fn(self, *args, **kwargs):
            lock = getattr(self, lock_name)
            with lock:
                return f(self, *args, **kwargs)
        return synchronized_fn
    return decorator

def get_formatted_zoom(zoom):
    text = locale.format('%5.2f', zoom * 100)
    for i in range(len(text)):
        if text[-1] == '0':
            text = text[:-1]
        if text[-1] not in string.digits:
            text = text[:-1]
            break
    return text + '%'

def monkeypatch_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

def format_exception(exception, tb):
    try:
        msg = exception.get_custom_msg()
    except AttributeError:
        #if sys.platform == 'win32' and isinstance(exception, WindowsError):
        #    #Python bug (fixed on 3.0), the error is not unicode
        #    msg = str(exception).decode('mbcs')
        #else:
            msg = str(exception)
    if msg == '':
        msg = exception.__class__.__name__
    #Due to the bug above, unicode coercing tb might fail. Take a safe approach.
    #tb = tb.decode('ascii', 'ignore')
    return msg, tb
