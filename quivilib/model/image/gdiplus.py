import sys
import logging
import wx
from quivilib.util import rescale_by_size_factor

log = logging.getLogger('gdiplus')


if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes
    gdiplus = ctypes.windll.gdiplus
    
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int)

    class GdiplusStartupInput(ctypes.Structure):
        _fields_ = [
                ('GdiplusVersion', ctypes.c_uint),
                ('DebugEventCallback', ctypes.c_void_p),
                ('SuppressBackgroundThread', wintypes.BOOL),
                ('SuppressExternalCodecs', wintypes.BOOL),
        ]

        def __init__(self):
            ctypes.Structure.__init__(self)
            self.GdiplusVersion = 1
            self.DebugEventCallback = None
            self.SuppressBackgroundThread = 0
            self.SuppressExternalCodecs = 0
                
    StartupInput = GdiplusStartupInput()
    token = ctypes.c_ulong()
    gdiplus.GdiplusStartup(ctypes.pointer(token), ctypes.pointer(StartupInput), None)


class _GdiPlusInnerImage(object):
    def __init__(self, path=None, istream=None):
        assert (path is None) ^ (istream is None)
        self.img = ctypes.c_void_p()
        if istream:
            gdiplus.GdipLoadImageFromStream(istream, ctypes.byref(self.img))
        elif path:
            gdiplus.GdipLoadImageFromFile(path, ctypes.byref(self.img))
        if not self.img:
            raise EnvironmentError("Unable to open image")
        
    def __del__(self):
        if hasattr(self, 'img') and self.img:
            gdiplus.GdipDisposeImage(self.img)
            del self.img

class GdiPlusImage(object):
    def __init__(self, canvas_type, f=None, path=None, img=None, delay=False):
        import pythoncom
        from win32com.server import util
        self.canvas_type = canvas_type

        if img is None:
            #TODO: load from f
            try:
                #Note - this will only work if path is a real file, and not an archive entry.
                img = _GdiPlusInnerImage(path=path)
            except EnvironmentError:
                if not f:
                    raise
                fs = util.FileStream(f)
                istream = util.wrap(fs, pythoncom.IID_IStream)
                #"ctypes.ArgumentError: argument 1: Don't know how to convert parameter 1"
                #If this ever worked, it's dead now.
                img = _GdiPlusInnerImage(istream=istream)
        
        width = ctypes.c_uint()
        gdiplus.GdipGetImageWidth(img.img, ctypes.byref(width))
        height = ctypes.c_uint()
        gdiplus.GdipGetImageHeight(img.img, ctypes.byref(height))
        
        self._original_width = self._width = width.value
        self._original_height = self._height = height.value
        
        self.img = img
        self.zoomed_bmp = None
        self.delay = delay
        self.rotation = 0

    @staticmethod
    def extensions():
        #Taken from https://docs.microsoft.com/en-us/windows/win32/api/gdiplusheaders/nf-gdiplusheaders-image-image(constwchar_bool)
        #Webp (and possibly others) don't work but should. They display in Paint, which I understand is basically a wrapper around GDI.
        return ['.bmp', '.emf', '.gif', '.jpg', '.jpeg', '.png', '.tiff']
        
    @property
    def width(self):
        if self.rotation in (0, 2):
            return self._width
        return self._height

    @property
    def height(self):
        if self.rotation in (0, 2):
            return self._height
        return self._width
        
    @property
    def original_width(self):
        if self.rotation in (0, 2):
            return self._original_width
        return self._original_height

    @property
    def original_height(self):
        if self.rotation in (0, 2):
            return self._original_height
        return self._original_width
        
    def delayed_load(self) -> None:
        self.delay = False
        
    def resize(self, width: int, height: int) -> None:
        if self._original_width == width and self._original_height == height:
            self.zoomed_bmp = None
        else:
            self.zoomed_bmp = self._resize_img(width, height)
        self._width = width
        self._height = height
        
    def _resize_img(self, width, height):
        if self.rotation in (1, 3):
            vwidth, vheight = height, width
        else:
            vwidth, vheight = width, height
        zoomed_bmp = wx.Bitmap(vwidth, vheight, 24)
        dc = wx.MemoryDC(zoomed_bmp)
        assert dc.IsOk()
        #hdc = dc.GetHDC()
        hdc = ctypes.c_ulong(dc.GetHandle()).value
        graphics = ctypes.c_void_p()
        gdiplus.GdipCreateFromHDC(hdc, ctypes.byref(graphics))
        assert graphics
        gdiplus.GdipSetInterpolationMode(graphics, 7)
        arr = (ctypes.c_int * 6)(*self._get_rotated_coords(0, 0, width, height))
        gdiplus.GdipDrawImagePointsI(graphics, self.img.img, arr, 3)
        gdiplus.GdipDeleteGraphics(graphics)
        return zoomed_bmp
        
    def resize_by_factor(self, factor: float) -> None:
        width = int(self._original_width * factor)
        height = int(self._original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise: int) -> None:
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        if self.zoomed_bmp:
            self.zoomed_bmp = self._resize_img(self.width, self.height)
        
    def paint(self, dc, x: int, y: int) -> None:
        if self.zoomed_bmp:
            dc.DrawBitmap(self.zoomed_bmp, x, y)
        elif self.img:
            #hdc = dc.GetHDC()
            hdc = ctypes.c_ulong(dc.GetHandle()).value
            graphics = ctypes.c_void_p()
            gdiplus.GdipCreateFromHDC(hdc, ctypes.byref(graphics))
            assert graphics
            gdiplus.GdipSetInterpolationMode(graphics, 7)
            arr = (ctypes.c_int * 6)(*self._get_rotated_coords(x, y, self._width, self._height))
            gdiplus.GdipDrawImagePointsI(graphics, self.img.img, arr, 3)
            gdiplus.GdipDeleteGraphics(graphics)
            
    def copy(self) -> ImageHandler:
        return GdiPlusImage(self.canvas_type, img=self.img)
    
    def copy_to_clipboard(self) -> None:
        bmp = wx.Bitmap(self._width, self._height, 24)
        dc = wx.MemoryDC(bmp)
        assert dc.IsOk()
        #hdc = dc.GetHDC()
        hdc = ctypes.c_ulong(dc.GetHandle()).value
        graphics = ctypes.c_void_p()
        gdiplus.GdipCreateFromHDC(hdc, ctypes.byref(graphics))
        assert graphics
        gdiplus.GdipSetInterpolationMode(graphics, 7)
        gdiplus.GdipDrawImage(graphics, self.img.img, 0, 0)
        gdiplus.GdipDeleteGraphics(graphics)
        data = wx.BitmapDataObject(bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            
    def create_thumbnail(self, width: int, height: int, delay: bool):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        if factor > 1:
            factor = 1
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        bmp = wx.Bitmap(width, height, 24)
        dc = wx.MemoryDC(bmp)
        assert dc.IsOk()
        #hdc = dc.GetHDC()
        hdc = ctypes.c_ulong(dc.GetHandle()).value
        graphics = ctypes.c_void_p()
        gdiplus.GdipCreateFromHDC(hdc, ctypes.byref(graphics))
        assert graphics
        gdiplus.GdipSetInterpolationMode(graphics, 5)
        gdiplus.GdipDrawImageRectI(graphics, self.img.img, 0, 0, width, height)
        gdiplus.GdipDeleteGraphics(graphics)
        return bmp
    
    def close(self):
        self.img = None

    def _get_rotated_coords(self, x, y, w, h):
        if self.rotation == 0:
            return x, y, x + w, y, x, y + h
        elif self.rotation == 1:
            return x + h, y, x + h, y + w, x, y
        elif self.rotation == 2:
            return x + w, y + h, x, y + h, x + w, y
        elif self.rotation == 3:
            return x, y + w, x, y, x + h, y + w 
        else:
            assert False, "invalid rotation"
