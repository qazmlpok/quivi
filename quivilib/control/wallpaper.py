#TODO: (1,3) Add: option to detect best background color
#TODO: (3,4) Add: multiple monitor support

import sys
import re
from pathlib import Path
import logging as log
from subprocess import Popen, PIPE, call

import wx
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.interface.imagehandler import ImageHandler, BaseImageProt
from quivilib.model import App
from quivilib.model.canvas import WallpaperCanvas
from quivilib.model.commandenum import FitSettings
from quivilib.control.canvas import WallpaperCanvasController
from quivilib.model import image

WALLPAPER_FILE_NAME = 'Quivi Wallpaper.bmp'

fit_choices: list[tuple[FitSettings.WallpaperFitType, str]] = [
    (FitSettings.WallpaperFitType.SCREEN_NONE, _("&Actual size")),
    (FitSettings.WallpaperFitType.TILED, _("&Tiled")),
    (FitSettings.WallpaperFitType.SCREEN_CROP_EXCESS, _("Stretch to fit screen, c&rop excess")),
    (FitSettings.WallpaperFitType.SCREEN_SHOW_ALL, _("Stretch to &fit screen, show entire image")),
]


class WallpaperController(object):
    def __init__(self, model: App):
        self.model = model
        self.img: ImageHandler|None = None
        self.canvas = WallpaperCanvas('wpcanvas', None)
        self.canvas_controller = None
        Publisher.subscribe(self.on_dialog_opened, 'wallpaper.dialog_opened')
        Publisher.subscribe(self.on_set_wallpaper, 'wallpaper.set')
        Publisher.subscribe(self.on_wallpaper_zoom, 'wallpaper.zoom')
        Publisher.subscribe(self.on_preview_position_changed, 'wallpaper.preview_position_changed')
        #Track the main canvas's image.
        Publisher.subscribe(self.on_image_loaded, 'canvas.image.loaded')
        
    def open_dialog(self):
        choices_str = [x[1] for x in fit_choices]
        if self.img:
            color = _get_bg_color()
            Publisher.sendMessage('wallpaper.open_dialog', choices=choices_str, color=color)

    def on_image_loaded(self, *, img: ImageHandler):
        self.img = img

    def on_dialog_opened(self, *, dialog):
        #canvas_view is a CanvasAdapter with a width and height property.
        self.canvas.view = dialog.canvas_view
        self.canvas_controller = WallpaperCanvasController('wpcanvas', self.canvas, dialog.canvas_view)
        self.canvas.load_img(self.img.copy(), False)
        
    def on_set_wallpaper(self, *, pos_idx: int, color: wx.Colour):
        position = fit_choices[pos_idx][0]
        
        item_index = self.model.container.selected_item_index
        path = self.model.container.items[item_index].path
        f = self.model.container.open_image(item_index)
        #can't use "with" because not every file-like object used here supports it
        img: BaseImageProt
        try:
            #This uses a direct PIL/FreeImage image object, not the ImageHandler interface
            #or associated logic.
            img = image.open_base_image(f, path)
        finally:
            f.close()
        if not img:
            return
        geo = wx.Display(0).GetGeometry()
        img = self.resize_image(img, position, geo.width, geo.height)
        img = self.move_image(img, position, color)
        _set_wallpaper(img, position, color)
        
    def on_preview_position_changed(self, *, pos_idx: int):
        fit_type = fit_choices[pos_idx][0]
        self.canvas_controller.set_zoom_by_fit_type(fit_type, wx.Display(0).GetGeometry().width)
    
    def on_wallpaper_zoom(self, *, zoom_in: bool):
        if zoom_in:
            self.canvas_controller.zoom_in()
        else:
            self.canvas_controller.zoom_out()
        
    def resize_image(self, img: BaseImageProt, position, screen_width, screen_height):
        zoom = self.canvas.zoom
        zoom *= self.preview_scale
        if zoom != 1:
            width = int(img.width * zoom)
            height = int(img.height * zoom)
            width = max(width, 1)
            height = max(height, 1)
            img = img.rescale(width, height)
        return img
    
    def move_image(self, img: BaseImageProt, position: FitSettings.WallpaperFitType, color: wx.Colour):
        left = int(self.canvas.left * self.preview_scale)
        top = int(self.canvas.top * self.preview_scale)
        if position == FitSettings.WallpaperFitType.TILED:
            if left == 0 and top == 0:
                #If the img is at the top-left (i.e. the user did not move it) let the Desktop handle the tiling.
                return img
            nleft = left % img.width
            ntop = top % img.height
            nimg = img.AllocateNew(img.width, img.height, 24)
            #Copy SE quadrant
            pimg = img.copy_region(0, 0, img.width - nleft, img.height - ntop)
            nimg.paste(pimg, nleft, ntop)
            #Copy NE quadrant
            pimg = img.copy_region(0, img.height - ntop, img.width - nleft, img.height)
            nimg.paste(pimg, nleft, 0)
            #Copy SW quadrant
            pimg = img.copy_region(img.width - nleft, 0, img.width, img.height - ntop)
            nimg.paste(pimg, 0, ntop)
            #Copy NW quadrant
            pimg = img.copy_region(img.width - nleft, img.height - ntop, img.width, img.height)
            nimg.paste(pimg, 0, 0)
            return nimg
        else:
            if self.canvas.centered:
                #If the img is centered (i.e. the user did not move it) let the Desktop handle the positioning.
                return img
            width = wx.Display(0).GetGeometry().width
            height = wx.Display(0).GetGeometry().height
            nimg = img.AllocateNew(width, height, 24)
            if color != (0, 0, 0):
                nimg.fill(color)
            nimg.paste(img, left, top)
            return nimg
        
    @property
    def preview_scale(self):
        return wx.Display(0).GetGeometry().width / float(self.canvas.view.width)


def _set_wallpaper(img, position: FitSettings.WallpaperFitType, color: wx.Colour):
    path = Path(wx.StandardPaths.Get().GetUserLocalDataDir())
    path.mkdir(parents=True, exist_ok=True)
    filename = path / WALLPAPER_FILE_NAME
    img.save_bitmap(str(filename))
    
    if sys.platform == 'win32':
        _set_windows_wallpaper(filename, position, color)
    else:
        _set_linux_wallpaper(filename, position, color)

def _get_bg_color() -> wx.Colour:
    if sys.platform == 'win32':
        color =  _get_windows_bg_color()
    else:
        color = _get_linux_bg_color()
    if color is None:
        log.debug("Error fetching desktop bg color")
        color = wx.Colour(0, 0, 0)
    return color    

def _get_linux_bg_color() -> wx.Colour:
    color = Popen('gsettings get org.gnome.desktop.background primary-color'.split(),
                  stdout=PIPE, stderr=open('/dev/null'), text=True).communicate()[0]
    log.debug("gconf color: " + color)
    m1 = re.match(r"^'?#([0-9a-fA-F]{12})'?", color)
    m2 = re.match(r"^'?#([0-9a-fA-F]{6})'?", color)
    if m1:
        color = m1.group(1)
        r = int(color[0:2], 16)
        g = int(color[4:6], 16)
        b = int(color[8:10], 16)
        color = wx.Colour(r, g, b)
    elif m2:
        color = m2.group(1)
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        color = wx.Colour(r, g, b)
    else:
        color = wx.Colour(0, 0, 0)
        log.warning("Couldn't match color %s as a color" % color)
    print("color", color, type(color))
    log.debug("gconf color processed: " + str(color))
    return color

def _set_linux_wallpaper(filename: Path, position: FitSettings.WallpaperFitType, color: wx.Colour):
    #Update image URI
    call('gsettings set org.gnome.desktop.background picture-uri'.split() + [f"'{filename}'"],
          stdout=PIPE, stderr=PIPE)
    #Change to tiled/centered
    option = 'wallpaper' if position == FitSettings.WallpaperFitType.TILED else 'centered'
    call('gsettings set org.gnome.desktop.background picture-options'.split() + [f"'{option}'"],
         stdout=PIPE, stderr=PIPE)
    color = [hex(color[0])[2:], hex(color[1])[2:], hex(color[2])[2:]]
    for i in range(3):
        s = color[i]
        if len(s) == 1:
            s = '0' + s
        color[i] = s
    color = '#' + ''.join(color)
    log.debug('gconf color set: ' + color)
    #Updddate primary color
    call('gsettings set org.gnome.desktop.background primary-color'.split() + [f"'{color}'"],
         stdout=PIPE, stderr=PIPE)

def _get_windows_bg_color() -> wx.Colour:
    import win32con, win32api
    color = win32api.GetSysColor(win32con.COLOR_BACKGROUND)
    color = wx.Colour(color)
    return color

def _set_windows_wallpaper(filename: Path, position: FitSettings.WallpaperFitType, color: wx.Colour):
    import win32gui, win32con, win32api, winreg
    tile_wallpaper = '1' if position == FitSettings.WallpaperFitType.TILED else '0'
    wallpaper_style = '0'
    desktopKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 'Control Panel\\Desktop', 0,
                                 winreg.KEY_SET_VALUE)
    winreg.SetValueEx(desktopKey, 'WallpaperStyle', 0, winreg.REG_SZ,
                       wallpaper_style)
    winreg.SetValueEx(desktopKey, 'TileWallpaper', 0, winreg.REG_SZ,
                       tile_wallpaper)
    win32api.SetSysColors((win32con.COLOR_BACKGROUND,), (win32api.RGB(*color),))
    res = win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER,
                            filename,
                            win32con.SPIF_UPDATEINIFILE |
                            win32con.SPIF_SENDCHANGE)
    if res is not None:
        raise RuntimeError(_('Unable to set wallpaper'))
