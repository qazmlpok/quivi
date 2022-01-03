from __future__ import absolute_import

from quivilib import meta

import logging as log
import traceback
import sys



IMG_CLASSES = []
if 'win' in sys.platform and meta.USE_GDI_PLUS:
    from quivilib.model.image.gdiplus import GdiPlusImage
    IMG_CLASSES.append(GdiPlusImage)
if meta.USE_CAIRO:
    from quivilib.model.image.cairo import CairoImage
    IMG_CLASSES.append(CairoImage)
if meta.USE_PIL:
    from quivilib.model.image.pil import PilImage
    IMG_CLASSES.append(PilImage)
if meta.USE_FREEIMAGE:
    from quivilib.model.image.freeimage import FreeImage
    IMG_CLASSES.append(FreeImage)



supported_extensions = []

def get_supported_extensions():
    exts = []
    if meta.USE_FREEIMAGE:
        from pyfreeimage import library
        exts += library.load().get_readable_extensions()
    if meta.USE_PIL:
        exts += ['.bmp', '.cur', '.dcx', '.fli', '.flc', '.fpx', '.gbr', '.gif',
                 '.ico', '.im', '.imt', '.jpg', '.jpeg', '.pcd', '.pcx', '.png',
                 '.ppm', '.pbm', '.pgm', '.sgi', '.tga', '.tif', '.tiff', '.xmb',
                 '.xpm']
    return list(set(exts))

supported_extensions = get_supported_extensions()



def open(f, path, canvas_type, delay=False):
    for cls in IMG_CLASSES:
        try:
            img = cls(canvas_type, f, path, delay=delay)
            break
        except Exception, e:
            if IMG_CLASSES[-1] is cls:
                raise
            else:
                log.debug(traceback.format_exc())
    return img
