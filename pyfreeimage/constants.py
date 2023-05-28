#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"The contents of this file are subject to the FreeImage Public License
Version 1.0 (the "License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at
http://home.wxs.nl/~flvdberg/freeimage-license.txt

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
the specific language governing rights and limitations under the License. 
"""

# Project       FreeImagePy
# file name:    constants.py
#
# $Id $
#
# DESCRIPTION
# FreeImage python bind
#
# Developer:
# Michele Petrazzo <michele.petrazzo@unipex.it>
#
# History :
# creation: 08/2005 - Michele Petrazzo
#
# License:
#         GNU General Public License (GPL)
#         FreeImage Public License (FIPL)
#         For more info see LICENSE.txt
#
# Copyright (C) 2005  Unipex s.r.l.,  All Rights Reserved.
# Via Vittorio Veneto 83/A
# 33050 Gonars (UD) - Italy
# tel. +39 0432 931511 - fax +39 0432 931378
# www.unipex.it - michele.petrazzo@unipex.it
#
import ctypes as C
import os, sys

from sys import platform as _platform

if _platform == 'win32':
    DLL_CALLCONV = C.WINFUNCTYPE
else:
    DLL_CALLCONV = C.CFUNCTYPE



"""
Internal types
"""
VOID    = C.c_void_p
INT     = C.c_int
BOOL    = C.c_long
BYTE    = C.c_ubyte
WORD    = C.c_ushort
DWORD   = C.c_ulong
LONG    = C.c_long

fi_handle = C.POINTER(C.c_void_p)
BYTE_P = C.POINTER(BYTE)

"""
Bitmap fif types
"""
FIF_UNKNOWN = -1
FIF_BMP		= 0
FIF_ICO		= 1
FIF_JPEG	= 2
FIF_JNG		= 3
FIF_KOALA	= 4
FIF_LBM		= 5
FIF_IFF = FIF_LBM
FIF_MNG		= 6
FIF_PBM		= 7
FIF_PBMRAW	= 8
FIF_PCD		= 9
FIF_PCX		= 10
FIF_PGM		= 11
FIF_PGMRAW	= 12
FIF_PNG		= 13
FIF_PPM		= 14
FIF_PPMRAW	= 15
FIF_RAS		= 16
FIF_TARGA	= 17
FIF_TIFF	= 18
FIF_WBMP	= 19
FIF_PSD		= 20
FIF_CUT		= 21
FIF_XBM		= 22
FIF_XPM		= 23
FIF_DDS		= 24
FIF_GIF     = 25
FIF_HDR		= 26
FIF_FAXG3	= 27
FIF_SGI		= 28

FIFTotype = { -1 : "UNKNOWN", 0  : "BMP", 1  : "ICO", 2  : "JPEG", 3  : "JNG",
        4  : "KOALA", 5 : "LBM | IFF", 6 : "MNG", 7  : "BPM", 8 : "PBMRAW",
        9  : "PCD", 10 : "PCX", 11 : "PGM", 12 : "PGMRAW", 13 : "PNG",
        14 : "PPM", 15 : "PPMRAW", 16 : "RAS", 17 : "TARGA", 18 : "TIFF",
        19 : "WBMP", 20 : "PSD", 21 : "CUT", 22 : "XBM", 23 : "XPM",
        24 : "DDS", 25 : "GIF", 26 : "HDR", 27 : "FAXG3", 28 : "SGI"}

FIF_MUTLIPAGE = (FIF_TIFF, FIF_ICO, FIF_GIF)
"""
Load / Save flag constants
"""
#Bmp
BMP_DEFAULT         = 0
BMP_SAVE_RLE        = 1

#Png
PNG_DEFAULT         = 0
PNG_IGNOREGAMMA		= 1

#Gif
GIF_DEFAULT			= 0
GIF_LOAD256			= 1
GIF_PLAYBACK		= 2

#Ico
ICO_DEFAULT         = 0
ICO_MAKEALPHA		= 1

#Tiff 
TIFF_DEFAULT        = 0
TIFF_CMYK           = 0x0001
TIFF_NONE           = 0x0800 
TIFF_PACKBITS       = 0x0100 
TIFF_DEFLATE        = 0x0200 
TIFF_ADOBE_DEFLATE  = 0x0400 
TIFF_CCITTFAX3      = 0x1000 
TIFF_CCITTFAX4      = 0x2000 
TIFF_LZW            = 0x4000	
TIFF_JPEG           = 0x8000

#Jpeg 
JPEG_DEFAULT        = 0
JPEG_FAST           = 1
JPEG_ACCURATE       = 2
JPEG_QUALITYSUPERB  = 0x80
JPEG_QUALITYGOOD    = 0x100
JPEG_QUALITYNORMAL  = 0x200
JPEG_QUALITYAVERAGE = 0x400
JPEG_QUALITYBAD     = 0x800
JPEG_CMYK			= 0x1000
JPEG_PROGRESSIVE	= 0x2000

#Others...
CUT_DEFAULT         = 0
DDS_DEFAULT			= 0
HDR_DEFAULT			= 0
IFF_DEFAULT         = 0
KOALA_DEFAULT       = 0
LBM_DEFAULT         = 0
MNG_DEFAULT         = 0
PCD_DEFAULT         = 0
PCD_BASE            = 1
PCD_BASEDIV4        = 2
PCD_BASEDIV16       = 3
PCX_DEFAULT         = 0
PNM_DEFAULT         = 0
PNM_SAVE_RAW        = 0
PNM_SAVE_ASCII      = 1
PSD_DEFAULT         = 0
RAS_DEFAULT         = 0
TARGA_DEFAULT       = 0
TARGA_LOAD_RGB888   = 1
WBMP_DEFAULT        = 0
XBM_DEFAULT			= 0



"""
Extension to type
See save (Image class) or loadAndSave (freeimage class) function

string: type, args and extension

"""

extToType = {
             "tiff"   : (FIF_TIFF, TIFF_DEFAULT,          '.tif'),
             "tiffg3" : (FIF_TIFF, TIFF_CCITTFAX3,        '.tif'),
             "tiffg4" : (FIF_TIFF, TIFF_CCITTFAX4,        '.tif'),
             "tiffno" : (FIF_TIFF, TIFF_NONE,             '.tif'),
             
             "jpeg"   : (FIF_JPEG, JPEG_DEFAULT,          '.jpg'),
             "jpegfa" : (FIF_JPEG, JPEG_FAST,             '.jpg'),
             "jpegac" : (FIF_JPEG, JPEG_ACCURATE,         '.jpg'),
             "jpegsu" : (FIF_JPEG, JPEG_QUALITYSUPERB,    '.jpg'),
             "jpeggo" : (FIF_JPEG, JPEG_QUALITYGOOD,      '.jpg'),
             "jpegav" : (FIF_JPEG, JPEG_QUALITYAVERAGE,   '.jpg'),
             "jpegba" : (FIF_JPEG, JPEG_QUALITYBAD,       '.jpg'),
             
             "png"    : (FIF_PNG,  PNG_DEFAULT,           '.png'),

             "bmp"    : (FIF_BMP,  BMP_DEFAULT,           '.bmp'),

             "ico"    : (FIF_ICO,  ICO_DEFAULT,           '.ico'),

             "gif"    : (FIF_GIF,  GIF_DEFAULT,           '.gif'),

             "pbm"    : (FIF_PBM,  PNM_DEFAULT,           '.pbm'),
             "pgm"    : (FIF_PGM,  PNM_DEFAULT,           '.pgm'),
             "pnm"    : (FIF_PPM,  PNM_DEFAULT,           '.pnm'),
             "ppm"    : (FIF_PPM,  PNM_DEFAULT,           '.ppm'),
        }


#Internal C structures
class FITAG(C.Structure):
    _fields_ = [ ("data",   VOID)]


#Are us little endian?
#import library
#_FI = library.internlLibrary()
LITTLEENDIAN = 1
#LITTLEENDIAN = _FI.IsLittleEndian()
#del _FI


class RGBQUAD(C.Structure):
    _fields_ = [] 
    if LITTLEENDIAN:
        _fields_ += [("rgbBlue",     BYTE),
                     ("rgbGreen",    BYTE),
                     ("rgbRed",      BYTE)]
    else:
        _fields_ += [("rgbRed",      BYTE),
                     ("rgbGreen",    BYTE),
                     ("rgbBlue",     BYTE)]
        
    _fields_ += [ ("rgbReserved", BYTE) ]
    
class FIBITMAP(C.Structure):
    _fields_ = [ ("data",   C.POINTER(VOID)) ]

class FIMETADATA(C.Structure):
    _fields_ = [ ("data", VOID ), ]        

class PBITMAPINFOHEADER(C.Structure):
    _fields_ = [ ("biSize",             DWORD ),
                 ("biWidth",            LONG  ),
                 ("biHeight",           LONG  ),
                 ("biPlanes",           WORD  ),
                 ("biBitCount",         WORD  ),
                 ("biCompression",      DWORD ),
                 ("biSizeImage",        DWORD ),
                 ("biXPelsPerMeter",    LONG  ),
                 ("biYPelsPerMeter",    LONG  ),
                 ("biClrUsed",          DWORD ),
                 ("biClrImportant",     DWORD ), ]
    
"""
Dither transformation

Floyd & Steinberg error diffusion
Bayer ordered dispersed dot dithering (order 2 dithering matrix)
Bayer ordered dispersed dot dithering (order 3 dithering matrix)
Ordered clustered dot dithering (order 3 - 6x6 matrix)
Ordered clustered dot dithering (order 4 - 8x8 matrix)
Ordered clustered dot dithering (order 8 - 16x16 matrix)
Bayer ordered dispersed dot dithering (order 4 dithering matrix)
"""
FID_FS		 = 0
FID_BAYER4x4	 = 1
FID_BAYER8x8	 = 2
FID_CLUSTER6x6	 = 3
FID_CLUSTER8x8	 = 4
FID_CLUSTER16x16 = 5
FID_BAYER16x16   = 6

#Get_type
FIC_MINISWHITE = 0
FIC_MINISBLACK = 1
FIC_RGB        = 2
FIC_PALETTE    = 3
FIC_RGBALPHA   = 4
FIC_CMYK       = 5

FICTotype = {0 : "MINISWHITE", 1 : "MINISBLACK", 2 : "RGB", 3 : "PALETTE", 
             4 : "RGBALPHA", 5 : "CMYK",}
"""
Filter for rescale:

Box, pulse, Fourier window, 1st order (constant) b-spline
Mitchell & Netravali's two-param cubic filter
Bilinear filter
4th order (cubic) b-spline
Catmull-Rom spline, Overhauser spline
Lanczos3 filter
"""

FILTER_BOX	  = 0
FILTER_BICUBIC	  = 1
FILTER_BILINEAR   = 2
FILTER_BSPLINE	  = 3
FILTER_CATMULLROM = 4
FILTER_LANCZOS3	  = 5

#Format type
FIT_UNKNOWN     = 0
FIT_BITMAP      = 1
FIT_UINT16	= 2
FIT_INT16	= 3
FIT_UINT32	= 4
FIT_INT32	= 5
FIT_FLOAT	= 6
FIT_DOUBLE	= 7
FIT_COMPLEX	= 8
FIT_RGB16	= 9
FIT_RGBA16	= 10
FIT_RGBF	= 11
FIT_RGBAF	= 12

#Metadata
FIMD_NODATA		    = -1
FIMD_COMMENTS		= 0
FIMD_EXIF_MAIN		= 1
FIMD_EXIF_EXIF		= 2
FIMD_EXIF_GPS		= 3
FIMD_EXIF_MAKERNOTE = 4
FIMD_EXIF_INTEROP	= 5
FIMD_IPTC	    	= 6
FIMD_XMP		    = 7
FIMD_GEOTIFF		= 8
FIMD_ANIMATION		= 9
FIMD_CUSTOM		    = 10

FIMD__METALIST = {"FIMD_NODATA": FIMD_NODATA, "FIMD_COMMENTS":FIMD_COMMENTS, 
                  "FIMD_EXIF_MAIN":FIMD_EXIF_MAIN, "FIMD_EXIF_EXIF": FIMD_EXIF_EXIF,
                  "FIMD_EXIF_GPS": FIMD_EXIF_GPS, "FIMD_EXIF_MAKERNOTE": FIMD_EXIF_MAKERNOTE,
                  "FIMD_EXIF_INTEROP": FIMD_EXIF_INTEROP,"FIMD_IPTC": FIMD_IPTC,
                  "FIMD_XMP": FIMD_XMP, "FIMD_GEOTIFF": FIMD_GEOTIFF,
                  "FIMD_ANIMATION": FIMD_ANIMATION, "FIMD_CUSTOM": FIMD_CUSTOM}

FIDT_NOTYPE     = 0    #// placeholder
FIDT_BYTE       = 1    #// 8-bit unsigned integer
FIDT_ASCII      = 2    #// 8-bit bytes w/ last byte null
FIDT_SHORT      = 3    #// 16-bit unsigned integer
FIDT_LONG       = 4    #// 32-bit unsigned integer
FIDT_RATIONAL   = 5    #// 64-bit unsigned fraction
FIDT_SBYTE      = 6    #// 8-bit signed integer
FIDT_UNDEFINED  = 7    #// 8-bit untyped data
FIDT_SSHORT     = 8    #// 16-bit signed integer
FIDT_SLONG      = 9    #// 32-bit signed integer
FIDT_SRATIONAL  = 10   #// 64-bit signed fraction
FIDT_FLOAT      = 11   #// 32-bit IEEE floating point
FIDT_DOUBLE     = 12   #// 64-bit IEEE floating point
FIDT_IFD        = 13   #// 32-bit unsigned integer (offset)
FIDT_PALETTE    = 14   #// 32-bit RGBQUAD

FIDT__LIST = {FIDT_NOTYPE: VOID, FIDT_BYTE: C.c_ubyte, FIDT_ASCII: C.c_char_p,
              FIDT_SHORT: C.c_ushort, FIDT_LONG: C.c_uint, FIDT_RATIONAL: C.c_ulong, 
              FIDT_SBYTE: C.c_short, FIDT_UNDEFINED: VOID, FIDT_SSHORT: C.c_short,
              FIDT_SLONG: C.c_long, FIDT_SRATIONAL: C.c_long, FIDT_FLOAT: C.c_float,
              FIDT_DOUBLE: C.c_double, FIDT_IFD: C.c_uint, FIDT_PALETTE: RGBQUAD }


#FREE_IMAGE_COLOR_CHANNEL
FICC_RGB	= 0
FICC_RED	= 1
FICC_GREEN	= 2
FICC_BLUE	= 3
FICC_ALPHA	= 4
FICC_BLACK	= 5
FICC_REAL	= 6
FICC_IMAG	= 7
FICC_MAG	= 8
FICC_PHASE	= 9

"""
FREE_IMAGE_QUANTIZE:

Xiaolin Wu color quantization algorithm
NeuQuant neural-net quantization algorithm by Anthony Dekker
"""

FIQ_WUQUANT = 0
FIQ_NNQUANT = 1

# Little Endian (x86 / MS Windows, Linux) : BGR(A) order
if LITTLEENDIAN:
    FI_RGBA_RED		        = 2
    FI_RGBA_GREEN		    = 1
    FI_RGBA_BLUE		    = 0
    FI_RGBA_ALPHA		    = 3
    FI_RGBA_RED_MASK	    = 0x00FF0000
    FI_RGBA_GREEN_MASK	    = 0x0000FF00
    FI_RGBA_BLUE_MASK	    = 0x000000FF
    FI_RGBA_ALPHA_MASK	    = 0xFF000000
    FI_RGBA_RED_SHIFT	    = 16
    FI_RGBA_GREEN_SHIFT	    = 8
    FI_RGBA_BLUE_SHIFT	    = 0
    FI_RGBA_ALPHA_SHIFT	    = 24
else:
    FI_RGBA_RED		        = 0
    FI_RGBA_GREEN		    = 1
    FI_RGBA_BLUE		    = 2
    FI_RGBA_ALPHA		    = 3
    FI_RGBA_RED_MASK	    = 0xFF000000
    FI_RGBA_GREEN_MASK	    = 0x00FF0000
    FI_RGBA_BLUE_MASK	    = 0x0000FF00
    FI_RGBA_ALPHA_MASK	    = 0x000000FF
    FI_RGBA_RED_SHIFT	    = 24
    FI_RGBA_GREEN_SHIFT	    = 16
    FI_RGBA_BLUE_SHIFT	    = 8
    FI_RGBA_ALPHA_SHIFT	    = 0

#My costatants

#Colors used in a bitmap
COL_1  = 1
COL_4  = 4
COL_8  = 8
COL_16 = 16
COL_24 = 24
COL_32 = 32
COL_48 = 48
COL_64 = 64
COL_96 = 96
COL_1TO8 = (COL_1, COL_4, COL_8)
COL_16TO32 = (COL_16, COL_24, COL_32)
COL_1TO32 = (COL_1, COL_4, COL_8, COL_16, COL_24, COL_32)
COL_1TO48 = COL_1TO32 + (COL_48, )

#Pil correspondence values
COL_To_PIL = {COL_1: "1", COL_8: "L", COL_24: "RGB", COL_32: "RGBA"}


ROTATE_ANGLE_1BIT = (-90, 90, 180, 270)


#Internal class structure

class FISize(object):
    """ A class used for store width and height bitmap informations
    """ 
    def __init__(self, valW=0, valH=0):
        """ Pass me the width and height
        """
        if type(valW) == int:
            self.__W, self.__H = valW, valH
        elif len(valW) == 2:
            self.__W, self.__H = valW
        else:
            raise ValueError
    
    def getWidth(self):
        return self.__W

    def getHeight(self):
        return self.__H
    
    def getSize(self):
        return (self.__W, self.__H)
    
    def __repr__(self):
        """
        """
        return f"FISize ({self.getWidth()}, {self.getHeight()})"

    def __len__(self):
        """
        """
        return 2
    
    def __iter__(self):
        """
        """
        yield self.__W
        yield self.__H
    
    def __eq__(self, other):
        """
        """
        if not isinstance(other, FISize):
            return False
        else:
            #print other.w == self.getWidth(), other.h == self.getHeight()
            return other.w == self.getWidth() and other.h == self.getHeight()
    
    def __hash__(self):
        return hash(self.__W, self.__H)
    
    w = property(getWidth)
    h = property(getHeight)
    size = property(getSize)


class FIPoint(object):
    """ A class used for store a point information
    """ 
    def __init__(self, valX=0, valY=0):
        """ Pass me the x and y
        """
        if type(valX) == int:
            self.__X, self.__Y = valX, valY
        elif len(valY) == 2:
            self.__X, self.__Y = valX
        else:
            raise ValueError
    
    def getX(self):
        return self.__X

    def getY(self):
        return self.__Y
    
    def getPoint(self):
        return (self.__X, self.__Y)
    
    def __eq__(self, other):
        """
        """
        print("point", other)
        
    def __hash__(self):
        return hash(self.__X, self.__Y)
    
    def __repr__(self):
        """
        """
        return "FIPoint (%i, %i)" % (self.getX(), self.getY())
    
    def __len__(self):
        """
        """
        return 2

    def __iter__(self):
        """
        """
        yield self.__X
        yield self.__Y
    
    x = property(getX)
    y = property(getY)
    point = property(getPoint)


FI_ReadProc = DLL_CALLCONV(C.c_uint, BYTE_P, C.c_uint, C.c_uint, fi_handle)
FI_WriteProc = DLL_CALLCONV(C.c_uint, BYTE_P, C.c_uint, C.c_uint, fi_handle)
FI_SeekProc = DLL_CALLCONV(C.c_int, fi_handle, C.c_long, C.c_int)
FI_TellProc = DLL_CALLCONV(C.c_long, fi_handle)

class FreeImageIO(C.Structure):
    _fields_ = [('read_proc', FI_ReadProc),
                ('write_proc', FI_WriteProc),
                ('seek_proc', FI_SeekProc),
                ('tell_proc', FI_TellProc)]

#Custom exceptions
class FreeImagePy_LibraryNotFound(Exception):
    """ 
        Exception raised then I don't found the library
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FreeImagePy_ColorWrong(Exception):
    """ 
        Exception raised then a function receive a wrong color depth
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FreeImagePy_RotateError(FreeImagePy_ColorWrong):
    """
       Rotate exeception because I can't rotate with this color depth
    """

class IOAttributeError(AttributeError):
    """
        IO operation won't wrok
    """

#Custom warnings
class FunctionNotFound(UserWarning):
    """
        Warning shown when I not found a library function
    """

class AutomaticDepthChange(UserWarning):
    """
        Warning shown when I change the bitmap depth into another BPP
    """

class TypeNotFound(UserWarning):
    """
        Warning shown when I not found the type passed into the type's list
    """
