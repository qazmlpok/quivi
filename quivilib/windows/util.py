import wx
import sys
import ctypes



def get_icon_for_extension(extension, small=True):
    """dot is mandatory in extension"""
    from win32com.shell import shell, shellcon
    from win32con import FILE_ATTRIBUTE_NORMAL, FILE_ATTRIBUTE_DIRECTORY
    
    flags = shellcon.SHGFI_ICON | shellcon.SHGFI_USEFILEATTRIBUTES
    flags |= (shellcon.SHGFI_SMALLICON if small else shellcon.SHGFI_LARGEICON)

    retval, info = shell.SHGetFileInfo(extension,
                             FILE_ATTRIBUTE_NORMAL,
                             flags)
    # non-zero on success
    assert retval

    hicon, iicon, attr, display_name, type_name = info

    # Get the bitmap
    icon = wx.Icon()
    icon.SetHandle(hicon)
    return icon

def get_icon_for_directory(small=True):
    from win32com.shell import shell, shellcon
    from win32con import FILE_ATTRIBUTE_NORMAL, FILE_ATTRIBUTE_DIRECTORY
    
    flags = shellcon.SHGFI_ICON | shellcon.SHGFI_USEFILEATTRIBUTES
    flags |= (shellcon.SHGFI_SMALLICON if small else shellcon.SHGFI_LARGEICON)

    retval, info = shell.SHGetFileInfo('dummy',
                             FILE_ATTRIBUTE_DIRECTORY,
                             flags)
    # non-zero on success
    assert retval

    hicon, iicon, attr, display_name, type_name = info

    # Get the bitmap
    icon = wx.Icon()
    icon.SetHandle(hicon)
    return icon

def logical_cmp(a, b):
    assert isinstance(a, str) and isinstance(b, str) 
    return ctypes.windll.shlwapi.StrCmpLogicalW(a, b)

def delete_file(path, window):
    from win32com.shell import shell, shellcon
    
    hwnd = window.GetHandle()
    flags = shellcon.FOF_ALLOWUNDO
    shell.SHFileOperation((hwnd, shellcon.FO_DELETE, path, None, flags, None, None))
