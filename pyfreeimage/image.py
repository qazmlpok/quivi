import ctypes
import logging as log

from pyfreeimage import library
import pyfreeimage.constants as CO
from pyfreeimage.buffer import FileIO


class Image(object):
    @classmethod
    def allocate(cls, width, height, bpp, red_mask=0, green_mask=0, blue_mask=0):
        lib = library.load()
        dib = lib.Allocate(width, height, bpp, red_mask, green_mask, blue_mask)
        if not dib:
            raise RuntimeError('Unable to allocate image')
        return cls(dib)
        
    @classmethod
    def load(cls, path, flags = 0):
        lib = library.load()
        fif = lib.GetFileType(path, 0)
        if fif == CO.FIF_UNKNOWN:
            fif = lib.GetFIFFromFilename(path)
        dib = None
        if fif != CO.FIF_UNKNOWN and lib.FIFSupportsReading(fif):
            dib = lib.Load(fif, path, flags)
        if not dib:
            raise RuntimeError('Unable to open image')
        return cls(dib)

    @classmethod
    def load_from_file(cls, f, filename_hint = None, flags = 0):
        lib = library.load()
        fileIO = FileIO(lib, f)
        fif = fileIO.getType()
        if fif == CO.FIF_UNKNOWN and filename_hint:
            fif = lib.GetFIFFromFilename(filename_hint)
        dib = None
        if fif != CO.FIF_UNKNOWN and lib.FIFSupportsReading(fif):
            dib = fileIO.load(fif, flags)
        if not dib:
            raise RuntimeError('Unable to open image')
        return cls(dib)
    
    def __init__(self, dib):
        self._lib = library.load()
        self._dib = dib

    def save_bitmap(self, path):
        return self.save(path, fif=CO.FIF_BMP)
    def save(self, path, flags = 0, fif = CO.FIF_UNKNOWN):
        lib = self._lib
        dib = self._dib
        #TODO: (1,2) Improve: Add option to try to change BPP, etc, to save?
        if fif == CO.FIF_UNKNOWN:
            fif = lib.GetFIFFromFilename(path)
        if fif == CO.FIF_UNKNOWN:
            raise RuntimeError('Unable to guess image format from file name for saving')    
        image_type = lib.GetImageType(dib)
        if image_type == CO.FIT_BITMAP:
            bpp = lib.GetBPP(dib)
            can_save = (lib.FIFSupportsWriting(fif)
                        and lib.FIFSupportsExportBPP(fif, bpp))
        else:
            can_save = lib.FIFSupportsExportType(fif, image_type)
        if not can_save:
            raise RuntimeError('Format specified for saving does not support the image')
        success = lib.Save(fif, dib, path, flags)
        if not success:
            raise RuntimeError('Unable to save image')
    
    @property
    def bpp(self):
        return self._lib.GetBPP(self._dib)
        
    def colortype(self):
        return self._lib.GetColorType(self._dib)()
    
    @property
    def pitch(self):
        return self._lib.GetPitch(self._dib)
    
    @property
    def width(self):
        return self._lib.GetWidth(self._dib)
    
    @property
    def width_bytes(self):
        return self._lib.GetLine(self._dib)
    
    @property
    def height(self):
        return self._lib.GetHeight(self._dib)
    
    @property
    def red_mask(self):
        return self._lib.GetRedMask(self._dib)
    
    @property
    def green_mask(self):
        return self._lib.GetGreenMask(self._dib)
    
    @property
    def transparent(self):
        return self._lib.IsTransparent(self._dib) == 1
    
    @property
    def blue_mask(self):
        return self._lib.GetBlueMask(self._dib)
    
    @property
    def bits(self):
        #TODO: (1,2) Improve: wrap in a ctypes object?
        return self._lib.GetBits(self._dib)
    
    @property
    def info(self):
        return self._lib.GetInfoHeader(self._dib)
    
    def convert_to_32_bits(self):
        dib = self._lib.ConvertTo32Bits(self._dib)
        if not dib:
            raise RuntimeError('Unable to convert image to 32 bits')
        return self.__class__(dib)
    
    def convert_to_24_bits(self):
        dib = self._lib.ConvertTo24Bits(self._dib)
        if not dib:
            raise RuntimeError('Unable to convert image to 24 bits')
        return self.__class__(dib)
    
    def convert_to_raw_bits(self, width_bytes=None):
        if width_bytes is None:
            width_bytes = self.width_bytes
        else:
            #freeimage and cairo may use different stride values.
            width_bytes = max(width_bytes, self.width_bytes)
        #Note - Stride: the number of bytes between the start of rows in the buffer as allocated.
        #In other words, the length in bytes of a row in the image, _padded for alignment_
        buf = ctypes.create_string_buffer(self.height * width_bytes)
        buf_idx = ctypes.addressof(buf)
        for line_idx in range(self.height-1, -1, -1):
            line_buf = self._lib.GetScanLine(self._dib, line_idx)
            ctypes.memmove(buf_idx, line_buf, width_bytes)
            buf_idx += width_bytes
        return buf
        
    def convert_to_wx_bitmap(self, wx):
        #TODO: (1,4) Improve: handle another types of bitmaps
        if self.bpp == 32:
            img = self
            img_format = wx.BitmapBufferFormat_ARGB32
        #elif self.bpp == 24:
        #Sigh. Still not working correctly.
        #    img = self
        #    img_format = wx.BitmapBufferFormat_RGB
        else:
            img = self.convert_to_32_bits()
            img_format = wx.BitmapBufferFormat_ARGB32
        width, height, bpp, pitch = img.width, img.height, img.bpp, img.pitch
        buf = img.convert_to_raw_bits()
        if img is not self:
            del img
        bmp = wx.Bitmap(width, height, bpp)
        bmp.CopyFromBuffer(buf, img_format, pitch)
        return bmp
    
    def convert_to_cairo_surface(self, cairo):
        img = self
        img_format = cairo.Format.ARGB32
        if self.bpp == 8:
            #In theory this can be done to avoid a conversion... but it's not working. It inverts the colors.
            #img_format = cairo.Format.A8
            img = self.convert_to_32_bits()
        elif self.bpp != 32:
            img = self.convert_to_32_bits()
        stride = img_format.stride_for_width(img.width)
        width, height = img.width, img.height
        b = img.convert_to_raw_bits(width_bytes=stride)
        surface = cairo.ImageSurface.create_for_data(b, img_format, width, height)
        
        if img is not self:
            del img
        return surface
    
    def maybeConvert32bit(self):
        """ Convert this image to 32 bit if it isn't already. This is needed because many operations
        require 32 bit ARGB images.
        TODO: Ideally conversions are only done if necessary, i.e. if the requestor can handle 8-bit
        grayscale, add that as a parameter and don't convert it.
        Possibly relevant (for cairo): https://stackoverflow.com/a/12384135 ?
        TODO: Consider returning a wrapper class that supports with so the img can be auto-disposed
        iff it was a clone.
        """
        if self.bpp != 32:
            return self.convert_to_32_bits()
        return self
    
    def AllocateNew(self, *args, **kwargs):
        """ Forward to static implementation. Needed for polymorphism.
        """
        return Image.allocate(*args, **kwargs)

    def rescale(self, width, height, resampling_filter=CO.FILTER_BICUBIC):
        dib = self._lib.Rescale(self._dib, width, height, resampling_filter)
        if not dib:
            raise RuntimeError('Unable to rescale image')
        return self.__class__(dib)
    
    def rotate(self, angle):
        dib = self._lib.Rotate(self._dib, ctypes.c_double(angle))
        if not dib:
            raise RuntimeError('Unable to rescale image')
        return self.__class__(dib)
    
    def composite(self, use_file_bg = False, app_bg_color = None, bg = None):
        dib = self._lib.Composite(self._dib, use_file_bg, app_bg_color, bg)
        if not dib:
            raise RuntimeError('Unable to composite image')
        return self.__class__(dib)
    
    def copy_region(self, left, top, right, bottom):
        dib = self._lib.Copy(self._dib, left, top, right, bottom)
        if not dib:
            raise RuntimeError('Unable to copy image')
        return self.__class__(dib)
    
    def paste(self, src, left, top, alpha=256):
        copy_required = False
        nleft = left
        ntop = top
        cleft = 0
        ctop = 0
        cwidth = src.width
        cheight = src.height
        if left < 0:
            copy_required = True
            cleft = -left
            nleft = 0
            cwidth -= cleft
        if top < 0:
            copy_required = True
            ctop = -top
            ntop = 0
            cheight -= ctop
        if left + src.width > self.width:
            copy_required = True
            cwidth -= (left + src.width - self.width)
        if top + src.height > self.height:
            copy_required = True
            cheight -= (top + src.height - self.height)
        if copy_required:
            src = src.copy_region(cleft, ctop, cleft + cwidth, ctop + cheight)
        res = self._lib.Paste(self._dib, src._dib, nleft, ntop, alpha)
        if not res:
            raise RuntimeError('Unable to paste image')
        
    def fill(self, color):
        #TODO: (1,3) Improve: support other bpp; check masks
        (r, g, b) = color
        assert self.bpp == 24, 'Unsupported BPP for fill'
        buf = ctypes.create_string_buffer(self.width_bytes)
        buf[0:(3 * (len(buf) / 3))] = [chr(b), chr(g), chr(r)] * (len(buf) / 3)
        buf_idx = ctypes.addressof(buf)
        for line_idx in range(self.height-1, -1, -1):
            line_buf = self._lib.GetScanLine(self._dib, line_idx)
            ctypes.memmove(line_buf, buf_idx, self.width_bytes)
        return buf
    
    def __getattr__(self, name):
        if name == "__array_interface__":
            dic = {}
            bypp = self.bpp / 8
            dic['shape'] = (self.height, self.width, bypp)
            dic['typestr'] = '|u1'
            data = ctypes.cast(self.bits, ctypes.c_void_p).value
            dic['data'] = (data, True)
            dic['strides'] = (self.pitch, bypp, 1)
            return dic
        raise AttributeError(name)
        
    def __del__(self):
        if self._dib:
            self._lib.Unload(self._dib)
            del self._dib
