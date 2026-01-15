import logging as log
import traceback
from pathlib import Path

from quivilib import meta

from quivilib.interface.imagehandler import ImageHandler, SecondaryImageHandler

IMG_CLASSES: list[type[SecondaryImageHandler]] = []
IMG_LOAD_CLASSES: list[type[ImageHandler]] = []

#if 'win' in sys.platform and meta.USE_GDI_PLUS:
#    from quivilib.model.image.gdiplus import GdiPlusImage
#    IMG_CLASSES.append(GdiPlusImage)
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


def open(f, path, delay=False) -> ImageHandler:
    """ Open the provided filehandle/path as an image.
    Wraps the image in a Cairo object if USE_CAIRO is True
    (This would also use GDI on Windows, if GDI was still supported)
    """
    ext = path.suffix
    img = open_direct(f, path, delay)

    # Skip Cairo wrapping for animated images (Cairo doesn't support animation)
    if hasattr(img, 'is_animated') and img.is_animated:
        return img

    for cls in IMG_CLASSES:
        try:
            img2 = cls(src=img, delay=delay)
            img = img2
            break
        except Exception:
            log.debug(traceback.format_exc())
    return img

def open_direct(f, path: Path, delay=False) -> ImageHandler:
    """ Open the provided filehandle/path as an image.
    PIL/Freeimage is used to open the image, depending on configuration.
    """
    ext = path.suffix.casefold()
    img = None
    for cls in IMG_LOAD_CLASSES:
        if not ext in cls.extensions():
            log.debug(f"Skip {cls} - no support for {ext}")
            continue
        try:
            img = cls(f, str(path), delay=delay)
            break
        except Exception:
            if IMG_LOAD_CLASSES[-1] is cls:
                raise
            else:
                log.debug(traceback.format_exc())
    if img is not None:
        return img
    raise Exception(f"Could not open {path} (unsupported extension?)")
