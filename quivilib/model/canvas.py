import traceback
import logging as log
import math
from functools import partial
from pubsub import pub as Publisher

from quivilib.model.settings import Settings
from quivilib.model import image
from quivilib.util import rescale_by_size_factor


#Number of scrolls at the top/bottom of the image needed to switch to horizontal scroll.
#Maybe a timestamp is more appropriate?
STICKY_LIMIT = 2
class Canvas(object):
    def __init__(self, name, settings):
        self.name = name
        if settings:
            self._get_int_setting = partial(settings.getint, 'Options')
            self._get_bool_setting = partial(settings.getboolean, 'Options')
        self.img = None
        self._zoom = 1
        self._left = 0
        self._top = 0
        self.sticky = 0
        self.view = None
        self._sendMessage(f'{self.name}.zoom.changed', zoom=self._zoom)

    def _sendMessage(self, topic, **kwargs):
        Publisher.sendMessage(topic, **kwargs)
        
    def set_view(self, view):
        """Set the physical canvas view being used.
        
        Model components should not know anything about the view, but
        Canvas has to be a exception. It needs to know the size of the physical
        canvas used to draw the image.
        
        The view isn't passed in the constructor because that would
        require the view to be passed to the model.App object. Instead,
        it is set by the MainController.
        
        @param view: the physical canvas
        @type view: an object with 'width' and 'height' attributes
        """
        self.view = view
        
    def load(self, f, path, adjust=True, delay=False):
        """ Load an image file (using either a file handle or a file path)
        into the canvas.
        Calls load_img after opening the file, using quivilib.model.image.open().
        """
        if __debug__:
            import time
            start = time.perf_counter()
        img = image.open(f, path, self.__class__, delay)
        #TODO: Return img instead of calling load_img directly.
        #This will avoid some unnecessary events from the cache (which nothing listens for)
        self.load_img(img, adjust)
        if __debug__:
            stop = time.perf_counter()
            log.debug(f'{path.name} took: {(stop - start)*1000:0.1f}ms.')
        
    def load_img(self, img, adjust=True):
        """ Sets an already loaded image (by `load` or equivalent)
        This is a separate function due to the cache: images can be load()ed before load_img()ed
        """
        self.img = img
        self._zoom = float(img.width) / float(img.original_width)
        self._sendMessage(f'{self.name}.zoom.changed', zoom=self._zoom)
        if adjust:
            self.adjust()
        self._sendMessage(f'{self.name}.image.loaded', img=self.img)
        self._sendMessage(f'{self.name}.changed')

    def adjust(self):
        fit_type = self._get_int_setting('FitType')
        self.set_zoom_by_fit_type(fit_type)
        
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1):
        if not self.img:
            return
        view_w = self.view.width
        view_h = self.view.height
        spread = self._get_bool_setting('DetectSpreads')
        img_w = self.img.original_width
        img_h = self.img.original_height
        is_spread = False
        if spread and img_w > (img_h * 1.3):
            #Normal page layout is taller than it is long. If this is not true,
            #assume it's two pages combined. display may be improved by calculating the width based on the "half" pages
            img_w = (img_w+1) // 2
            #Used for status bar updates. Will be reported even if it doesn't matter (e.g. fit height). Is this bad?
            is_spread = True

        if fit_type == Settings.FIT_WIDTH:
            factor = rescale_by_size_factor(img_w, img_h, view_w, 0)
            self.zoom = factor
        elif fit_type == Settings.FIT_HEIGHT:
            factor = rescale_by_size_factor(img_w, img_h, 0, view_h)
            self.zoom = factor
        elif fit_type == Settings.FIT_WIDTH_OVERSIZE:
            factor = rescale_by_size_factor(img_w, img_h, view_w, 0)
            factor = 1 if factor > 1 else factor
            self.zoom = factor
        elif fit_type == Settings.FIT_HEIGHT_OVERSIZE:
            factor = rescale_by_size_factor(img_w, img_h, 0, view_h)
            factor = 1 if factor > 1 else factor
            self.zoom = factor
        elif fit_type == Settings.FIT_BOTH_OVERSIZE:
            factor = rescale_by_size_factor(img_w, img_h, view_w, view_h)
            factor = 1 if factor > 1 else factor
            self.zoom = factor
        elif fit_type == Settings.FIT_BOTH:
            factor = rescale_by_size_factor(img_w, img_h, view_w, view_h)
            self.zoom = factor
        elif fit_type == Settings.FIT_CUSTOM_WIDTH:
            custom_w = self._get_int_setting('FitWidthCustomSize')
            factor = rescale_by_size_factor(img_w, img_h, custom_w, 0)
            factor = 1 if factor > 1 else factor
            self.zoom = factor
        elif fit_type == Settings.FIT_NONE:
            self.zoom = 1
        else:
            assert False, 'Invalid fit type: ' + str(fit_type)
        
        self.center()
        Publisher.sendMessage(f'{self.name}.fit.changed', FitType=fit_type, IsSpread=is_spread)

    def _zoom_image(self, zoom):
        """ Shared logic between zoom_to_center (default behavior) and zoom_to_point (new behavior)
        This is still kinda confused because zoom_to_center is used as a setter.
        Returns True if the zoom level changed. Caller needs to handle the left/top adjustment.
        """
        if zoom >= 0.01 and zoom <= 16 and not math.isclose(zoom, self._zoom, rel_tol=1e-05):
            original_zoom = self._zoom
            if math.isclose(zoom, 1, rel_tol=1e-03):
                #Done to clear potential floating point inaccuracies. In practice even 1e-07 should be enough.
                zoom = 1
                self._zoom = zoom
            else:
                self._zoom = zoom
            try:
                self.img.resize_by_factor(self._zoom)
            except Exception:
                #Revert without zooming
                log.debug(traceback.format_exc())
                self._zoom = original_zoom
                return False
            return True
        return False
    def zoom_to_point(self, zoom, x, y):
        old_w = self.width
        old_h = self.height
        if self._zoom_image(zoom):
            #This isn't perfect, as left and top are properties, and modify the value at times
            #but for the most part it works.
            self.left += int((old_w - self.width) * ((x-self.left) / old_w))
            self.top  += int((old_h - self.height) * ((y-self.top) / old_h))
            self._sendMessage(f'{self.name}.zoom.changed', zoom=self._zoom)
    def _set_zoom(self, zoom):
        #TODO: (1,3) Refactor: maybe this should be another method;
        #    like this, there are several places in this file where
        #    self._zoom is set and a message must be sent.
        #    So _set_zoom isn't always called when the zoom is set, so
        #    it should be renamed (probably to 'resize')
        old_w = self.width
        old_h = self.height
        if self._zoom_image(zoom):
            self.left += old_w // 2 - self.width // 2
            self.top += old_h // 2 - self.height // 2
            self._sendMessage(f'{self.name}.zoom.changed', zoom=self._zoom)
            
    def _get_zoom(self):
        return self._zoom
    
    zoom = property(_get_zoom, _set_zoom)
    
    @property
    def width(self):
        if self.img:
            return self.img.width
        else:
            return 0
    @property
    def height(self):
        if self.img:
            return self.img.height
        else:
            return 0

    def _set_left(self, left):
        img_w = self.width
        scr_w = self.view.width
        if scr_w:
            if img_w > scr_w:
                if left > 0:
                    left = 0
                elif left < scr_w - img_w:
                    left = scr_w - img_w
            else:
                if left < 0:
                    left = 0
                elif left > scr_w - img_w:
                    left = scr_w - img_w
        self._left = left
    def _get_left(self):
        return self._left
    left = property(_get_left, _set_left)
    
    def _set_top(self, top):
        img_h = self.height
        scr_h = self.view.height
        if scr_h:
            if img_h > scr_h:
                if top > 0:
                    top = 0
                elif top < scr_h - img_h:
                    top = scr_h - img_h
            else:
                if top < 0:
                    top = 0
                elif top > scr_h - img_h:
                    top = scr_h - img_h
        self._top = top
    def _get_top(self):
        return self._top
    top = property(_get_top, _set_top)
    
    def scroll_hori(self, amount, reverse_direction = False):
        """ Scrolls the canvas. Just calls _set_left.
        """
        if reverse_direction:
            amount = -amount
        self.left += amount
    
    def scroll_vert(self, amount, reverse_direction = False):
        """ Scrolls the canvas. Calls _set_top.
        However if the image is wider than the viewport and the canvas is already scrolled
        to the top (or bottom, depending on direction), it will instead scroll left/right.
        """
        if reverse_direction:
            amount = -amount
        old_top = self.top
        self.top += amount
        #If the scroll didn't move at all, scroll to the left/right instead (if possible)
        #To avoid accidental left/right scrolling, a counter is used to "delay" the scroll.
        side_scroll = self._get_bool_setting('HorizontalScrollAtBottom')
        if (old_top == self.top and self.width > self.view.width):
            self.sticky += 1
            if self.sticky > STICKY_LIMIT:
                rtl = self._get_bool_setting('UseRightToLeft')
                self.scroll_hori(amount, rtl)
        else:
            self.sticky = 0
        
    def center(self):
        #TODO: Should rename. This only centers if the img is smaller than the viewport
        scr_w = self.view.width
        scr_h = self.view.height
        img_w = self.width
        img_h = self.height
        if img_w > scr_w:
            rtl = self._get_bool_setting('UseRightToLeft')
            #align left (TODO: (1,4) Improve: customizable?
            if rtl:
                #Scroll all the way to the right
                self.left = scr_w - img_w
            else:
                self.left = 0
        else:
            #center
            self.left = scr_w // 2 - img_w // 2
        if img_h > scr_h:
            #align top
            self.top = 0
        else:
            #center
            self.top = scr_h // 2 - img_h // 2
        self.sticky = 0
    
    @property
    def y_centered(self):
        scr_h = self.view.height
        img_h = self.height
        return (self.top == scr_h // 2 - img_h // 2)
    @property
    def x_centered(self):
        scr_w = self.view.width
        img_w = self.width
        return (self.left == scr_w // 2 - img_w // 2)
    @property
    def centered(self):
        return self.x_centered and self.y_centered
    
    def copy_to_clipboard(self):
        if self.img is not None:
            self.img.copy_to_clipboard()

    def has_image(self):
        return self.img is not None

    def paint(self, dc):
        if not self.img:
            return
        else:
            self.img.paint(dc, self.left, self.top)
    
    def rotate(self, clockwise):
        if not self.img:
            return
        self.img.rotate(clockwise)
        #TODO: Add a configuration option to disable this adjust if zoomed in/out.
        #If I've zoomed in manually, I don't want this to reset the zoom.
        self.adjust()
        self._sendMessage(f'{self.name}.changed')

class WallpaperCanvas(Canvas):
    """ Special canvas used for the wallpaper dialog. This is completely separate from the display canvas
    It includes some additional fit modes that don't make sense for the standard image display.
    """
    def __init__(self, name, settings):
        super().__init__(name, settings)
        self.tiled = False
        #Wallpaper canvas won't include settings.
        self._get_int_setting = lambda x: 0
        self._get_bool_setting = lambda x: False
    def paint(self, dc):
        if not self.img:
            return
        #Wallpaper can additionally be tiled.
        if self.tiled:
            start_x = self.left % self.width
            if start_x > 0:
                start_x -= self.width
            start_y = self.top % self.height
            if start_y > 0:
                start_y -= self.height
            for x in range(start_x, self.view.width, self.width):
                for y in range(start_y, self.view.height, self.height):
                    self.img.paint(dc, x, y)
        else:
            super().paint(dc)
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1):
        #The wallpaper fit includes additional options. This is a full copy of the original code.
        #Except the spread code was removed; that doesn't make sense for the wallpaper.
        if not self.img:
            return
        view_w = self.view.width
        view_h = self.view.height
        spread = self._get_bool_setting('DetectSpreads')
        img_w = self.img.original_width
        img_h = self.img.original_height
        self.tiled = False

        if fit_type == Settings.FIT_SCREEN_CROP_EXCESS:
            if img_w / float(img_h) > view_w / float(view_h):
                factor = rescale_by_size_factor(img_w, img_h, 0, view_h)
            else:
                factor = rescale_by_size_factor(img_w, img_h, view_w, 0)
            self.zoom = factor
        elif fit_type == Settings.FIT_SCREEN_SHOW_ALL:
            factor = rescale_by_size_factor(img_w, img_h, view_w, view_h)
            self.zoom = factor
        elif fit_type == Settings.FIT_SCREEN_NONE:
            assert scr_w != -1, 'Screen width not specified'
            factor = view_w / float(scr_w)
            self.zoom = factor
        elif fit_type == Settings.FIT_TILED:
            assert scr_w != -1, 'Screen width not specified'
            factor = view_w / float(scr_w)
            self.zoom = factor
            self.tiled = True
        else:
            assert False, 'Invalid fit type: ' + str(fit_type)
        
        if self.tiled:
            self.left = self.top = 0
        else:
            self.center()
        Publisher.sendMessage(f'{self.name}.fit.changed', FitType=fit_type, IsSpread=False)
    #

class TempCanvas(Canvas):
    """ Used by the cache to load images. Suppresses most functionality
    This never needs to render, for example. 
    TODO: Which means, does it even need to be a canvas in the first place?
    """
    def __init__(self, name, settings):
        super().__init__(name, settings)
    def _sendMessage(self, topic, **kwargs):
        #Do not send messages (equivalent to the old 'quiet' parameter)
        pass
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1):
        #Explicitly do nothing. (the default implementation references the view to get screen width)
        pass
