from pathlib import Path

import wx.aui
from pubsub import pub as Publisher

from quivilib import util
from quivilib.control.options import get_fit_choices
from quivilib.i18n import _
from quivilib.interface.imagehandler import ImageHandler
from quivilib.model.container import Item
from quivilib.model.container.base import BaseContainer


# The status bar is split into four fields.
NAME_FIELD = 0
SIZE_FIELD = 1
ZOOM_FIELD = 2
FIT_FIELD = 3


class QuiviStatusBar(wx.StatusBar):
    def __init__(self, parent: wx.Window, ide=wx.ID_ANY, style=wx.STB_DEFAULT_STYLE, name=wx.StatusBarNameStr):
        super().__init__(parent, ide, style, name)

        self.SetFieldsCount(4)
        size_width = self.GetTextExtent('10000 x 10000')[0] + 10
        zoom_width = self.GetTextExtent('9999.99%')[0] + 20
        fit_width = self.GetTextExtent('Width if larger with added stuff')[0] + 20
        self.SetStatusWidths([-1, size_width, zoom_width, fit_width])

        Publisher.subscribe(self.on_canvas_fit_changed, 'canvas.fit.changed')
        Publisher.subscribe(self.on_canvas_zoom_changed, 'canvas.zoom.changed')
        Publisher.subscribe(self.on_container_opened, 'container.opened')
        Publisher.subscribe(self.on_image_opened, 'container.image.opened')
        Publisher.subscribe(self.on_image_loading, 'container.image.loading')
        Publisher.subscribe(self.on_image_loaded, 'canvas.image.loaded')

    def on_canvas_fit_changed(self, *, FitType, IsSpread=False):
        fit_choices = get_fit_choices()
        name = [name for name, typ in fit_choices if typ == FitType][0]
        txt = name
        if IsSpread:
            txt += ' ' + _('(Spread)')
        self.SetStatusText(txt, FIT_FIELD)

    def on_canvas_zoom_changed(self, *, zoom: float):
        text = util.get_formatted_zoom(zoom)
        self.SetStatusText(text, ZOOM_FIELD)

    def on_image_loading(self, *, item):
        self.SetStatusText(_('Loading...'), NAME_FIELD)

    def on_image_loaded(self, *, img: ImageHandler):
        if img is None:
            self.SetStatusText('', SIZE_FIELD)
            self.SetStatusText('', ZOOM_FIELD)
        else:
            width = img.base_width
            height = img.base_height
            self.SetStatusText('%d x %d' % (width, height), SIZE_FIELD)

    def on_container_opened(self, *, container: BaseContainer):
        self.SetStatusText(container.name, NAME_FIELD)

    def on_image_opened(self, *, item: Item):
        self.SetStatusText(str(item.full_path), NAME_FIELD)
