from pubsub import pub as Publisher

from quivilib.model.canvas.basecanvas import BaseCanvas
from quivilib.model.commandenum import FitSettings
from quivilib.util import rescale_by_size_factor


class WallpaperCanvas(BaseCanvas):
    """ Special canvas used for the wallpaper dialog. This is completely separate from the display canvas
    It includes some additional fit modes that don't make sense for the standard image display.
    """
    def __init__(self, name: str, settings):
        super().__init__(name, settings)
        self.tiled = False
        #Wallpaper canvas won't include settings.
        self._get_str_setting = lambda x: ''
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
            for x in range(start_x, self.view_width, self.width):
                for y in range(start_y, self.view_height, self.height):
                    self.img.paint(dc, x, y)
        else:
            super().paint(dc)

    def set_zoom_by_fit_type(self, fit_type: FitSettings.WallpaperFitType, scr_w = -1):
        #The wallpaper fit uses a different set of options.
        if not self.img:
            return

        view_w = self.view_width
        view_h = self.view_height
        img_w = self.img.base_width
        img_h = self.img.base_height
        self.tiled = False

        if fit_type == FitSettings.WallpaperFitType.SCREEN_CROP_EXCESS:
            if img_w / float(img_h) > view_w / float(view_h):
                factor = rescale_by_size_factor(img_w, img_h, 0, view_h)
            else:
                factor = rescale_by_size_factor(img_w, img_h, view_w, 0)
        elif fit_type == FitSettings.WallpaperFitType.SCREEN_SHOW_ALL:
            factor = rescale_by_size_factor(img_w, img_h, view_w, view_h)
        elif fit_type == FitSettings.WallpaperFitType.SCREEN_NONE:
            assert scr_w != -1, 'Screen width not specified'
            factor = view_w / float(scr_w)
        elif fit_type == FitSettings.WallpaperFitType.TILED:
            assert scr_w != -1, 'Screen width not specified'
            factor = view_w / float(scr_w)

            self.tiled = True
        else:
            assert False, 'Invalid fit type: ' + str(fit_type)

        self.zoom = factor
        if self.tiled:
            self.left = self.top = 0
        else:
            self.center()
        Publisher.sendMessage(f'{self.name}.fit.changed', FitType=fit_type, IsSpread=False)
    #
