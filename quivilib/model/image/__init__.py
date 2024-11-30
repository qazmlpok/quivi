import logging as log
import traceback
import sys

from quivilib import meta

IMG_CLASSES = []
IMG_LOAD_CLASSES = []
if 'win' in sys.platform and meta.USE_GDI_PLUS:
    from quivilib.model.image.gdiplus import GdiPlusImage
    IMG_CLASSES.append(GdiPlusImage)
if meta.USE_CAIRO:
    from quivilib.model.image.cairo import CairoImage
    IMG_CLASSES.append(CairoImage)
if meta.USE_PIL:
    from quivilib.model.image.pil import PilImage
    IMG_LOAD_CLASSES.append(PilImage)
if meta.USE_FREEIMAGE:
    from quivilib.model.image.freeimage import FreeImage
    IMG_LOAD_CLASSES.append(FreeImage)


supported_extensions = []
def get_supported_extensions():
    exts = []
    if meta.USE_FREEIMAGE:
        from pyfreeimage import library
        exts += library.load().get_readable_extensions()
    if meta.USE_PIL:
        #PIL.Image.registered_extensions(). This is a curated list.
        exts += ['.bmp', '.cur', '.dcx', '.fli', '.flc', '.fpx', '.gbr', '.gif', 
                 '.ico', '.im', '.imt', '.jpg', '.jpeg', '.pcd', '.pcx', '.png', '.apng',
                 #JPEG 2000. No JPEG XL support yet.
                 '.j2c', '.j2k', '.jfif', '.jp2', '.jpc', '.jpe', '.jpf', '.jpx',
                 '.ppm', '.pbm', '.pgm', '.sgi', '.tga', '.tif', '.tiff', '.xmb',
                 '.webp', '.xpm']
    return list(set(exts))

supported_extensions = get_supported_extensions()


def open(f, path, canvas_type, delay=False):
    """ Open the provided filehandle/path as an image.
    Wraps the image in a Cairo object if USE_CAIRO is True
    (This would also use GDI on Windows, if GDI was still supported)
    """
    ext = path.suffix
    img = open_direct(f, path, canvas_type, delay)
    for cls in IMG_CLASSES:
        try:
            img2 = cls(canvas_type, src=img, delay=delay)
            img = img2
            break
        except Exception as e:
            log.debug(traceback.format_exc())
    return img

def open_direct(f, path, canvas_type, delay=False):
    """ Open the provided filehandle/path as an image.
    PIL/Freeimage is used to open the image, depending on configuration.
    """
    ext = path.suffix
    img = None
    for cls in IMG_LOAD_CLASSES:
        if not ext in cls.extensions():
            log.debug(f"Skip {cls} - no support for {ext}")
            continue
        try:
            img = cls(canvas_type, f, str(path), delay=delay)
            break
        except Exception as e:
            if IMG_LOAD_CLASSES[-1] is cls:
                raise
            else:
                log.debug(traceback.format_exc())
    return img
