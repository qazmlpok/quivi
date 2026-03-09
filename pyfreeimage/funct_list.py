#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"The contents of this file are subject to the FreeImage Public License
Version 1.0 (the "License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at
https://freeimage.sourceforge.io/freeimage-license.txt

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
the specific language governing rights and limitations under the License. 
"""

#Functions list that now acutally wrap. The third value are the return
#type, if it exists, or if I'm able to translate from C code :)
import ctypes as C
from typing import Protocol, Any

from . import constants as CO

class FreeImageLibrary(Protocol):
    # Init / Error routines
    def Initialise(self, load_local_plugins_only=False) -> None:
        pass

    def DeInitialise(self) -> None:
        pass

    # Message output functions
    def SetOutputMessage(self, omf) -> None:
        pass

    def OutputMessageProc(self, fif, fmt, **kwargs) -> None:
        pass

    # Allocate / Clone / Unload routines
    def Allocate(self, width, height, bpp, red_mask=0, green_mask=0, blue_mask=0):
        pass

    def Clone(self, dib):
        pass

    def Unload(self, dib) -> None:
        pass

    # Load / Save
    def Load(self, fif, filename, flags=0):
        pass

    def LoadFromHandle(self, fif, io, handle, flags=0):
        pass

    def Save(self, fif, dib, filename, flags=0) -> bool:
        pass

    def GetFIFCount(self) -> int:
        pass

    def GetFIFFromFormat(self, fmt: bytes) -> int:
        pass

    def GetFormatFromFIF(self, fif) -> bytes:
        pass

    def GetFIFExtensionList(self, fif) -> bytes:
        pass

    def GetFIFDescription(self, fif) -> bytes:
        pass

    def GetFIFFromFilename(self, filename: bytes) -> int:
        pass

    def FIFSupportsReading(self, fif: int) -> bool:
        pass

    def FIFSupportsWriting(self, fif: int) -> bool:
        pass

    def FIFSupportsExportBPP(self, fif: int, bpp: int) -> bool:
        pass

    def FIFSupportsExportType(self, fif: int, typ) -> bool:
        pass

    # Multi-page
    def OpenMultiBitmap(self, fif, filename, create_new, read_only, keep_cache_in_memory=False, flags=0):
        pass

    def OpenMultiBitmapFromHandle(self, fif, io, handle, flags=0):
        pass

    def CloseMultiBitmap(self, bitmap, flags=0):
        pass

    def GetPageCount(self, bitmap):
        pass

    def LockPage(self, bitmap, page):
        pass

    def UnlockPage(self, bitmap, data, changed: bool):
        pass

    #
    def GetImageType(self, dib) -> int:
        # ret: enum FREE_IMAGE_FORMAT
        pass

    def GetFileType(self, filename, size=0) -> int:
        # ret: enum FREE_IMAGE_FORMAT
        pass

    def GetFileTypeFromHandle(self, io, handle, size=0) -> int:
        # ret: enum FREE_IMAGE_FORMAT
        pass

    def GetFileTypeFromMemory(self, stream, size=0) -> int:
        # ret: enum FREE_IMAGE_FORMAT
        pass

    # Pixel access routines
    def GetBits(self, dib):
        pass

    def GetScanLine(self, dib, scanline):
        pass

    # DIB info routines
    def GetColorsUsed(self, dib) -> int:
        pass

    def GetBPP(self, dib) -> int:
        pass

    def GetWidth(self, dib) -> int:
        pass

    def GetHeight(self, dib) -> int:
        pass

    def GetLine(self, dib) -> int:
        """Returns the width of the bitmap in bytes."""
        pass

    def GetPitch(self, dib) -> int:
        """Returns the width of the bitmap in bytes, rounded to the next 32-bit boundary"""
        pass

    def GetDIBSize(self, dib) -> int:
        pass

    def GetMemorySize(self, dib):
        pass

    def GetPalette(self, dib):
        pass

    def GetInfoHeader(self, dib):
        pass

    def GetInfo(self, dib):
        pass

    def GetColorType(self, dib):
        pass

    def GetRedMask(self, dib):
        pass

    def GetGreenMask(self, dib):
        pass

    def GetBlueMask(self, dib):
        pass

    def GetTransparencyCount(self, dib):
        pass

    def GetTransparencyTable(self, dib):
        pass

    def IsTransparent(self, dib):
        pass

    # Smart conversion routines
    def ConvertTo4Bits(self, dib):
        pass

    def ConvertTo8Bits(self, dib):
        pass

    def ConvertToGreyscale(self, dib):
        pass

    def ConvertTo16Bits555(self, dib):
        pass

    def ConvertTo16Bits565(self, dib):
        pass

    def ConvertTo24Bits(self, dib):
        pass

    def ConvertTo32Bits(self, dib):
        pass

    def ColorQuantize(self, dib, quantize):
        pass

    # Tags
    def GetTagKey(self, lp_tag) -> bytes:
        pass

    def GetTagDescription(self, lp_tag) -> bytes:
        pass

    def GetTagId(self, lp_tag) -> int:
        pass

    def GetTagType(self, lp_tag) -> CO.FreeImageMdModel:
        pass

    def GetTagCount(self, lp_tag) -> int:
        pass

    def GetTagLength(self, lp_tag) -> int:
        pass

    def GetTagValue(self, lp_tag) -> Any:
        pass

    # Metadata
    def FindFirstMetadata(self, model: CO.FreeImageMdModel, dib, lp_lp_tag) -> CO.FIMETADATA:
        pass

    def FindNextMetadata(self, lp_mdhandle, lp_lp_tag) -> bool:
        pass

    def FindCloseMetadata(self, lp_mdhandle) -> None:
        pass

    def GetMetadata(self, model: CO.FreeImageMdModel, dib, key: bytes, lp_lp_tag) -> bool:
        pass

    def GetMetadataCount(self, model: CO.FreeImageMdModel, dib) -> int:
        pass

    def TagToString(self, model: CO.FreeImageMdModel, lp_tag) -> bytes:
        pass

    # rotation and flipping, upsampling / downsampling
    def Rotate(self, dib, angle, bkcolor=None):
        pass

    def FlipHorizontal(self, dib) -> bool:
        pass

    def FlipVertical(self, dib) -> bool:
        pass

    def Rescale(self, dib, width, height, filt):
        pass

    def MakeThumbnail(self, dib, max_pixel_size):
        pass

    # copy / paste / composite routines
    def Copy(self, dib, left, top, right, bottom):
        pass

    def Paste(self, dst, src, left, top, alpha) -> bool:
        pass

    def Composite(self, fg, useFileBkg=False, appBkColor=None, bg=None):
        pass

    def FillBackground(self, dib, color, options=0) -> bool:
        pass


FUNCTION_LIST = ( 
    
    #General funtions
    ('FreeImage_Initialise',            '@4'), 
    ('FreeImage_DeInitialise',          '@0'),
    ('FreeImage_GetVersion',            '@0', None, C.c_char_p), 
    ('FreeImage_GetCopyrightMessage',   '@0', None, C.c_char_p), 
    ('FreeImage_SetOutputMessage',      '@4'),
    
    #Bitmap management functions
    ('FreeImage_Allocate',      '@24', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_AllocateT',     '@28', None, CO.fi_handle),
    ('FreeImage_Load',          '@12', None, CO.fi_handle),
    ('FreeImage_LoadU',         '@12', None, CO.fi_handle),
    ('FreeImage_LoadFromHandle','@16', None, CO.fi_handle),
    ('FreeImage_Save',          '@16', None, CO.BOOL),
    ('FreeImage_SaveU',         '@16', None, CO.BOOL),
    ('FreeImage_SaveToHandle',  '@20', None, CO.BOOL),
    ('FreeImage_Clone',         '@4', None, CO.fi_handle),
    ('FreeImage_Unload',        '@4', None, None),
    
    #Bitmap information
    ('FreeImage_GetImageType',          '@4'),
    ('FreeImage_GetColorsUsed',         '@4', CO.COL_1TO32 ),
    ('FreeImage_GetBPP',                '@4'),
    ('FreeImage_GetWidth',              '@4'),
    ('FreeImage_GetHeight',             '@4'),
    ('FreeImage_GetLine',               '@4'),
    ('FreeImage_GetPitch',              '@4'),
    ('FreeImage_GetDIBSize',            '@4'),
    ('FreeImage_GetPalette',            '@4', CO.COL_1TO32, 
        C.POINTER(CO.RGBQUAD) ),
    ('FreeImage_GetDotsPerMeterX',      '@4'),
    ('FreeImage_GetDotsPerMeterY',      '@4'),
    ('FreeImage_SetDotsPerMeterX',      '@8'), 
    ('FreeImage_SetDotsPerMeterY',      '@8'),
    ('FreeImage_GetInfo',               '@4', CO.COL_1TO32,
        C.POINTER(C.c_void_p)),
    ('FreeImage_GetInfoHeader',         '@4', CO.COL_1TO32,
        C.POINTER(CO.PBITMAPINFOHEADER)),
    ('FreeImage_GetColorType',          '@4', CO.COL_1TO32 ),
    ('FreeImage_GetRedMask',            '@4', CO.COL_1TO32 ),
    ('FreeImage_GetGreenMask',          '@4', CO.COL_1TO32 ),
    ('FreeImage_GetBlueMask',           '@4', CO.COL_1TO32 ),
    ('FreeImage_GetTransparencyCount',  '@4', CO.COL_1TO32 ),
    ('FreeImage_GetTransparencyTable',  '@4', (CO.COL_8,), C.POINTER(CO.BYTE)),
    ('FreeImage_SetTransparencyTable',  '@12', (CO.COL_8,) ),
    ('FreeImage_SetTransparent',        '@8', (CO.COL_8, CO.COL_32) ),
    ('FreeImage_IsTransparent',         '@4', CO.COL_1TO32 ),
    ('FreeImage_HasBackgroundColor',    '@4', (CO.COL_8, CO.COL_24, CO.COL_32) ),
    ('FreeImage_GetBackgroundColor',    '@8', (CO.COL_8, CO.COL_24, CO.COL_32),
        C.POINTER(CO.RGBQUAD) ),
    ('FreeImage_SetBackgroundColor',    '@8', (CO.COL_8, CO.COL_24, CO.COL_32) ),
    
    #Filetype functions
    ('FreeImage_GetFileType',           '@8'), 
    ('FreeImage_GetFileTypeU',          '@8'),
    ('FreeImage_GetFileTypeFromHandle', '@12'), 
    
    
    #Pixel access
    ('FreeImage_GetBits',       '@4',  None, C.POINTER(CO.BYTE)),
    ('FreeImage_GetScanLine',   '@8',  None, C.POINTER(CO.BYTE)),
    ('FreeImage_GetPixelIndex', '@16', CO.COL_1TO8 ),
    ('FreeImage_SetPixelIndex', '@16', CO.COL_1TO8 ),
    ('FreeImage_GetPixelColor', '@16', CO.COL_16TO32 ),
    ('FreeImage_SetPixelColor', '@16', CO.COL_16TO32 ),

    #Conversion / Trasformation
    ('FreeImage_ConvertTo4Bits',        '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ConvertTo8Bits',        '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ConvertToGreyscale',    '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ConvertTo16Bits555',    '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ConvertTo16Bits565',    '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ConvertTo24Bits',       '@4', CO.COL_1TO48, CO.fi_handle),
    ('FreeImage_ConvertTo32Bits',       '@4', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_ColorQuantize',         '@8', (CO.COL_24,)),
    ('FreeImage_ColorQuantizeEx',       '@20', (CO.COL_24,)),
    ('FreeImage_Threshold',             '@8', CO.COL_1TO32),
    ('FreeImage_Dither',                '@8', CO.COL_1TO32),
    ('FreeImage_ConvertFromRawBits',    '@36', CO.COL_1TO32),
    ('FreeImage_ConvertToRawBits',      '@32', CO.COL_1TO32),
    ('FreeImage_ConvertToStandardType', '@8'),
    ('FreeImage_ConvertToType',         '@12'),
    ('FreeImage_ConvertToRGBF',         '@4', (CO.COL_24, CO.COL_32,)),
    
    #Copy / Paste / Composite routines
    ('FreeImage_Copy',      '@20', None, CO.fi_handle),
    ('FreeImage_Paste',     '@20', CO.COL_1TO32, CO.BOOL),
    ('FreeImage_Composite',     '@16', (CO.COL_8, CO.COL_32), CO.fi_handle),
    
    #Plugin
    ('FreeImage_GetFIFCount',               '@0'),
    ('FreeImage_SetPluginEnabled',          '@8'),
    ('FreeImage_FIFSupportsReading',        '@4'), 
    ('FreeImage_GetFIFFromFilename',        '@4'),
    ('FreeImage_GetFIFFromFilenameU',       '@4'),
    ('FreeImage_FIFSupportsExportBPP',      '@8'),
    ('FreeImage_FIFSupportsExportType',     '@8'),
    ('FreeImage_FIFSupportsICCProfiles',    '@4'),
    ('FreeImage_FIFSupportsWriting',        '@4'),
    ('FreeImage_IsPluginEnabled',           '@4'),
    ('FreeImage_RegisterLocalPlugin',       '@20'),           
    ('FreeImage_GetFIFDescription',         '@4', None, C.c_char_p),
    ('FreeImage_GetFIFExtensionList',       '@4', None, C.c_char_p),
    ('FreeImage_GetFIFFromFormat',          '@4', None, C.c_char_p),
    ('FreeImage_GetFIFFromMime',            '@4', None, C.c_char_p),
    ('FreeImage_GetFIFMimeType',            '@4', None, C.c_char_p),
    ('FreeImage_GetFIFRegExpr',             '@4', None, C.c_char_p),
    ('FreeImage_GetFormatFromFIF',          '@4', None, C.c_char_p),
    
    #Upsampling / downsampling
    ('FreeImage_Rescale',       '@16', CO.COL_1TO32, CO.fi_handle ),
    ('FreeImage_MakeThumbnail', '@12', CO.COL_1TO32, CO.fi_handle ),
    
    #Rotation and flipping
    ('FreeImage_Rotate',        '@12', CO.COL_1TO32, CO.fi_handle),
    ('FreeImage_RotateEx',      '@48', (CO.COL_8, CO.COL_24, CO.COL_32), CO.fi_handle),

    
    #Color manipulation
    ('FreeImage_AdjustBrightness',  '@12', (CO.COL_8, CO.COL_24, CO.COL_32), CO.BOOL),
    ('FreeImage_AdjustCurve',       '@12', (CO.COL_8, CO.COL_24, CO.COL_32), CO.BOOL),
    ('FreeImage_AdjustGamma',       '@12', (CO.COL_8, CO.COL_24, CO.COL_32), CO.BOOL),
    ('FreeImage_AdjustContrast',    '@12', (CO.COL_8, CO.COL_24, CO.COL_32), CO.BOOL),
    ('FreeImage_GetHistogram',      '@12', (CO.COL_8, CO.COL_24, CO.COL_32), CO.BOOL),
    ('FreeImage_Invert',            '@4',  CO.COL_1TO32, CO.BOOL), 
    ('FreeImage_GetChannel',        '@8',  (CO.COL_24, CO.COL_32)),
    ('FreeImage_SetChannel',        '@12', (CO.COL_24, CO.COL_32)),
    ('FreeImage_GetComplexChannel', '@8'),
    ('FreeImage_SetComplexChannel', '@12'),
    
    #Multipage
    ('FreeImage_OpenMultiBitmap',       '@24'), 
    ('FreeImage_AppendPage',            '@8'), 
    ('FreeImage_CloseMultiBitmap',      '@8'), 
    ('FreeImage_GetPageCount',          '@4'),
    ('FreeImage_LockPage',              '@8'), 
    ('FreeImage_UnlockPage',            '@12'),
    ('FreeImage_InsertPage',            '@12'),
    ('FreeImage_DeletePage',            '@8'),
    ('FreeImage_MovePage',              '@12'),
    ('FreeImage_GetLockedPageNumbers',  '@12'),
    
    #Tag
    ('FreeImage_GetTagValue',       '@4'), 
    ('FreeImage_GetTagDescription', '@4',  None, C.c_char_p), 
    ('FreeImage_TagToString',       '@12', None, C.c_char_p),
    ('FreeImage_GetTagCount',       '@4',  None, CO.DWORD),
    ('FreeImage_GetTagKey',         '@4',  None, C.c_char_p),
    ('FreeImage_GetTagID',          '@4', None, C.c_char_p),
    ('FreeImage_GetTagType',        '@4'),
    
    
    #Metadata
    ('FreeImage_GetMetadata',       '@16'), 
    ('FreeImage_GetMetadataCount',  '@8', None, CO.DWORD),
    ('FreeImage_FindFirstMetadata', '@12', None, CO.VOID),
    ('FreeImage_FindNextMetadata',  '@8', None, CO.VOID),
    ('FreeImage_FindCloseMetadata', '@4'),
    
    ('FreeImage_IsLittleEndian',    '@0')
    
    # --------------- This functions don't work yet :(
    
    #All handle functions...
    
)
