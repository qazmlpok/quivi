

from quivilib.model.settings import Settings
from quivilib.model import image
from quivilib.util import rescale_by_size_factor

from wx.lib.pubsub import pub as Publisher

from functools import partial
import sys
import traceback
import logging as log
    



class Canvas(object):
     
    def __init__(self, name, settings, quiet=False):
        self.name = name
        self.quiet = quiet
        if settings:
            self._get_int_setting = partial(settings.getint, 'Options')
        self.img = None
        self._zoom = 1
        self._left = 0
        self._top = 0
        self.tiled = False
        self.view = None
        self._sendMessage('%s.zoom.changed' % self.name, self._zoom)
        
    def _sendMessage(self, topic, data):
        if not self.quiet:
            Publisher.sendMessage(topic, data)
        else:
            pass
        
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
        img = image.open(f, path, self.__class__, delay)
        self.load_img(img, adjust)
        
    def load_img(self, img, adjust=True):
        self.img = img
        self._zoom = float(img.width) / float(img.original_width)
        self._sendMessage('%s.zoom.changed' % self.name, self._zoom)
        if adjust:
            self.adjust()
        self._sendMessage('%s.image.loaded' % self.name,
                                (self.img.original_width, self.img.original_height))
        self._sendMessage('%s.changed' % self.name, None)
        
                          
    def adjust(self):
        fit_type = self._get_int_setting('FitType')
        self.set_zoom_by_fit_type(fit_type)
        
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1):
        if not self.img:
            return
        view_w = self.view.width
        view_h = self.view.height
        img_w = self.img.original_width
        img_h = self.img.original_height
        self.tiled = False
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
        elif fit_type == Settings.FIT_SCREEN_CROP_EXCESS:
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
        elif fit_type == Settings.FIT_NONE:
            self.zoom = 1
        else:
            assert False, 'Invalid fit type: ' + str(fit_type)
        if self.tiled:
            self.left = self.top = 0
        else:
            self.center()
        Publisher.sendMessage('%s.fit.changed' % self.name, fit_type)
        
    def _set_zoom(self, zoom):
        #TODO: (1,3) Refactor: maybe this should be another method;
        #    like this, there are several places in this file where
        #    self._zoom is set and an message must be sent.
        #    So _set_zoom isn't always called when the zoom is set, so
        #    it should be renamed (probably to 'resize')
        if zoom >= 0.01 and zoom <= 16 and abs(zoom - self._zoom) >= 0.01:
            old_w = self.width
            old_h = self.height
            original_zoom = self._zoom
            if abs(zoom - 1) < 0.01:
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
             
            self.left += old_w // 2 - self.width // 2
            self.top += old_h // 2 - self.height // 2
            self._sendMessage('%s.zoom.changed' %self.name, self._zoom)
            
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
        
    def center(self):
        scr_w = self.view.width
        scr_h = self.view.height
        img_w = self.width
        img_h = self.height
        if img_w > scr_w:
            #align left (TODO: (1,4) Improve: customizable?
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
        self.img.copy_to_clipboard()
        
    def paint(self, dc):
        if not self.img:
            return
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
            self.img.paint(dc, self.left, self.top)
    
    def rotate(self, clockwise):
        if not self.img:
            return
        self.img.rotate(clockwise)
        self.adjust()
        self._sendMessage('%s.changed' % self.name, None)
