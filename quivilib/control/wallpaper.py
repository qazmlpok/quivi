

#TODO: (1,3) Add: option to detect best background color
#TODO: (3,4) Add: multiple monitor support

from quivilib.i18n import _
from pathlib import Path
from quivilib.model.canvas import Canvas
from quivilib.model.settings import Settings
from quivilib.control.canvas import CanvasController
import pyfreeimage as fi
from quivilib.model.image.freeimage import FreeImage

import wx
from pubsub import pub as Publisher

import sys
import re
import logging as log
from subprocess import Popen, PIPE, call


WALLPAPER_FILE_NAME = 'Quivi Wallpaper.bmp'
#This list should reflect the list in open_dialog (same order)
positions = (Settings.FIT_SCREEN_NONE, Settings.FIT_TILED,
             Settings.FIT_SCREEN_CROP_EXCESS,
             Settings.FIT_SCREEN_SHOW_ALL)



class WallpaperController(object):
    def __init__(self, model):
        self.model = model
        self.canvas = Canvas('wpcanvas', None)
        Publisher.subscribe(self.on_dialog_opened, 'wallpaper.dialog_opened')
        Publisher.subscribe(self.on_set_wallpaper, 'wallpaper.set')
        Publisher.subscribe(self.on_wallpaper_zoom, 'wallpaper.zoom')
        Publisher.subscribe(self.on_preview_position_changed, 'wallpaper.preview_position_changed')
        
    def open_dialog(self):
        choices_str = [_("&Actual size"),
                       _("&Tiled"),
                       _("Stretch to fit screen, c&rop excess"),
                       _("Stretch to &fit screen, show entire image")]
        if self.model.canvas.img:
            color = _get_bg_color()
            Publisher.sendMessage('wallpaper.open_dialog', choices=choices_str, color=color)
            
    def on_dialog_opened(self, *, dialog):
        self.canvas.view = dialog.canvas_view
        self.canvas_controller = CanvasController('wpcanvas', self.canvas, dialog.canvas_view)
        self.canvas.load_img(self.model.canvas.img.copy(), False)
        
    def on_set_wallpaper(self, *, pos_idx, color):
        position = positions[pos_idx]
        
        item_index = self.model.container.selected_item_index
        path = self.model.container.items[item_index].path
        f = self.model.container.open_image(item_index)
        #can't use "with" because not every file-like object used here supports it
        img = None
        try:
            img = FreeImage(None, f=f, path=path).img
        finally:
            f.close()
        if not img:
            return
        img = self.resize_image(img, position,
                                wx.Display(0).GetGeometry().width,
                                wx.Display(0).GetGeometry().height)
        img = self.move_image(img, position, color)
        _set_wallpaper(img, position, color)
        
    def on_preview_position_changed(self, *, pos_idx):
        self.canvas_controller.set_zoom_by_fit_type(positions[pos_idx],
                                                    wx.Display(0).GetGeometry().width)
    
    def on_wallpaper_zoom(self, *, zoom_in):
        if zoom_in:
            self.canvas_controller.zoom_in()
        else:
            self.canvas_controller.zoom_out()
        
    def resize_image(self, img, position, screen_width, screen_height):
        zoom = self.canvas.zoom
        zoom *= self.preview_scale
        if zoom != 1:
            width = int(img.width * zoom)
            height = int(img.height * zoom)
            width = 1 if width < 1 else width
            height = 1 if height < 1 else height
            img = img.rescale(width, height,
                              fi.FILTER_BICUBIC)
        return img
    
    def move_image(self, img, position, color):
        left = int(self.canvas.left * self.preview_scale)
        top = int(self.canvas.top * self.preview_scale)
        if position == Settings.FIT_TILED:
            if left == 0 and top == 0:
                return img
            nleft = left % img.width
            ntop = top % img.height
            nimg = fi.Image.allocate(img.width, img.height, 24)
            #Copy SE quadrant
            pimg = img.copy(0, 0, img.width - nleft, img.height - ntop)
            nimg.paste(pimg, nleft, ntop)
            #Copy NE quadrant
            pimg = img.copy(0, img.height - ntop, img.width - nleft, img.height)
            nimg.paste(pimg, nleft, 0)
            #Copy SW quadrant
            pimg = img.copy(img.width - nleft, 0, img.width, img.height - ntop)
            nimg.paste(pimg, 0, ntop)
            #Copy NW quadrant
            pimg = img.copy(img.width - nleft, img.height - ntop, img.width, img.height)
            nimg.paste(pimg, 0, 0)
            return nimg
        else:
            if self.canvas.centered:
                return img
            width = wx.Display(0).GetGeometry().width
            height = wx.Display(0).GetGeometry().height
            nimg = fi.Image.allocate(width, height, 24)
            if color != (0, 0, 0):
                nimg.fill(color)
            nimg.paste(img, left, top)
            return nimg
        
    @property
    def preview_scale(self):
        return wx.Display(0).GetGeometry().width / float(self.canvas.view.width)



def _set_wallpaper(img, position, color):
    path = Path(wx.StandardPaths.Get().GetUserLocalDataDir())
    try:
        path.makedirs()
    except:
        pass
    filename = path / WALLPAPER_FILE_NAME
    img.save(filename, fif=fi.constants.FIF_BMP)
    
    if sys.platform == 'win32':
        _set_windows_wallpaper(filename, position, color)
    else:
        _set_linux_wallpaper(filename, position, color)

def _get_bg_color():
    if sys.platform == 'win32':
        color =  _get_windows_bg_color()
    else:
        color = _get_linux_bg_color()
    if color is None:
        log.debug("Error fetching desktop bg color")
        color = wx.Color(0, 0, 0)
    return color    

def _get_linux_bg_color():
    color = Popen('gconftool-2 -g /desktop/gnome/background/primary_color'.split(),
                  stdout=PIPE, stderr=open('/dev/null')).communicate()[0]
    log.debug("gconf color: " + color)
    if re.match('^#[0-9a-fA-F]{12}', color):
        r = int(color[1:3], 16)
        g = int(color[5:7], 16)
        b = int(color[9:11], 16)
        color = wx.Color(r, g, b)
    elif re.match('^#[0-9a-fA-F]{6}', color):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        color = wx.Color(r, g, b)
    log.debug("gconf color processed: " + str(color))
    return color

def _set_linux_wallpaper(filename, position, color):
    call('gconftool-2 -t str -s /desktop/gnome/background/picture_filename'.split() + [filename],
          stdout=PIPE, stderr=PIPE)
    option = 'wallpaper' if position == Settings.FIT_TILED else 'centered'
    call('gconftool-2 -t str -s /desktop/gnome/background/picture_options'.split() + [option],
         stdout=PIPE, stderr=PIPE)
    color = [hex(color[0])[2:], hex(color[1])[2:], hex(color[2])[2:]]
    for i in range(3):
        s = color[i]
        if len(s) == 1:
            s = '0' + s
        color[i] = s
    color = '#' + ''.join(color)
    log.debug('gconf color set: ' + color)
    call('gconftool-2 -t str -s /desktop/gnome/background/primary_color'.split() + [color],
         stdout=PIPE, stderr=PIPE)

def _get_windows_bg_color():
    import win32con, win32api
    color = win32api.GetSysColor(win32con.COLOR_BACKGROUND)
    color = wx.ColourRGB(color)
    return color

def _set_windows_wallpaper(filename, position, color):
    import win32gui, win32con, win32api, winreg
    tile_wallpaper = '1' if position == Settings.FIT_TILED else '0'
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