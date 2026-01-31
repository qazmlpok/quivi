import sys
import traceback
import logging as log
from pathlib import Path

import wx
import wx.aui
from pubsub import pub as Publisher

from quivilib import meta
from quivilib import util
from quivilib.control.options import get_fit_choices
from quivilib.gui.debug import DebugDialog
from quivilib.gui.file_list import FileListPanel
from quivilib.i18n import _
from quivilib.interface.canvasadapter import CanvasAdapter
from quivilib.model import Favorites
from quivilib.model.canvas import PaintedRegion
from quivilib.model.command import Command, CommandCategory
from quivilib.model.commandenum import MenuName, CommandName
from quivilib.model.container.base import BaseContainer
from quivilib.model.favorites import FavoriteMenuItem
from quivilib.model.settings import Settings
from quivilib.resources import images
from quivilib.util import error_handler

from typing import Any

# The status bar is split into four fields.
NAME_FIELD = 0
SIZE_FIELD = 1
ZOOM_FIELD = 2
FIT_FIELD = 3

def _handle_error(exception, args, kwargs):
    self = args[0]
    return self.handle_error(exception)


class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1, title=meta.APPNAME)
        self.aui_mgr = wx.aui.AuiManager()
        self.aui_mgr.SetManagedWindow(self)
        self.aui_mgr.SetFlags(self.aui_mgr.GetFlags() & ~wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE)

        bundle = wx.IconBundle()
        bundle.AddIcon(images.quivi16.Icon)
        bundle.AddIcon(images.quivi32.Icon)
        bundle.AddIcon(images.quivi48.Icon)
        bundle.AddIcon(images.quivi256.Icon)
        self.SetIcons(bundle)
        
        dt = self.QuiviFileDropTarget(self)
        self.SetDropTarget(dt)
        
        self.menu_bar = wx.MenuBar()
        self.SetMenuBar(self.menu_bar)
        
        self.status_bar = wx.StatusBar(self)
        self.SetStatusBar(self.status_bar)
        self.status_bar.SetFieldsCount(4)
        size_width = self.status_bar.GetTextExtent('10000 x 10000')[0] + 10
        zoom_width = self.status_bar.GetTextExtent('9999.99%')[0] + 20
        fit_width = self.status_bar.GetTextExtent('Width if larger with added stuff')[0] + 20
        self.status_bar.SetStatusWidths([-1, size_width, zoom_width, fit_width])
        
        self.file_list_panel = FileListPanel(self)
        self.aui_mgr.AddPane(self.file_list_panel, wx.aui.AuiPaneInfo().
                             Name('file_list').Caption(_('Files')).Left().
                             Layer(1).Position(0).CloseButton(True).
                             DestroyOnClose(False).BestSize(300, 400))
        
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.aui_mgr.AddPane(self.panel, wx.aui.AuiPaneInfo().Name("content").CenterPane())
        
        self.aui_mgr.Update()
        self.bindings_and_subscriptions()

        if __debug__:
            #This is created immediately because it listens for messages.
            self.dbg_dialog = DebugDialog(self)
        
        self._last_size = self.get_window_size()
        self._last_pos = self.GetPosition()     # NOTE - This has no effect on Wayland
        self._busy = False
        #List of (id, name) tuples. Filled on the favorites.changed event,
        #used in the file list popup menu
        self.favorites_menu_items: list[FavoriteMenuItem] = []
        self._favorite_menu_count = 0
        self.update_menu_item = None
        self.accel_table = None
        #Track as a dictionary
        self.menus: dict[MenuName, wx.Menu] = {}
        self.menu_names: dict[MenuName, str] = {}
        #Used for updating translations dynamically. Pair the actual wx objects and the local definitions.
        self.all_cmd_pairs: list[tuple[Command, wx.MenuItem]] = []
        #Set by a background task if there is an update available.
        self.down_url: str|None = None

    def bindings_and_subscriptions(self):
        self.panel.Bind(wx.EVT_PAINT, self.on_panel_paint)
        self.panel.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.panel.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self._bind_panel_mouse_events()
        self.panel.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.status_bar.Bind(wx.EVT_CONTEXT_MENU, self.on_fit_context_menu)

        Publisher.subscribe(self.on_busy, 'busy')
        Publisher.subscribe(self.on_error, 'error')
        Publisher.subscribe(self.on_freeze, 'gui.freeze')
        Publisher.subscribe(self.on_thaw, 'gui.thaw')
        Publisher.subscribe(self.on_container_opened, 'container.opened')
        Publisher.subscribe(self.on_image_opened, 'container.image.opened')
        Publisher.subscribe(self.on_image_loading, 'container.image.loading')
        Publisher.subscribe(self.on_image_loaded, 'canvas.image.loaded')
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_canvas_changed, 'canvas.changed')
        Publisher.subscribe(self.on_canvas_fit_changed, 'canvas.fit.changed')
        Publisher.subscribe(self.on_canvas_cursor_changed, 'canvas.cursor.changed')
        Publisher.subscribe(self.on_canvas_zoom_changed, 'canvas.zoom.changed')
        Publisher.subscribe(self.on_menu_built, 'menu.built')
        Publisher.subscribe(self.on_menu_labels_changed, 'menu.labels.changed')
        Publisher.subscribe(self.on_shortcuts_changed, 'menu.shortcuts.changed')
        Publisher.subscribe(self.on_cmd_context_menu, 'menu.context_menu')
        Publisher.subscribe(self.on_favorites_changed, 'favorites.changed')
        #Publisher.subscribe(self.on_favorite_settings_changed, 'settings.changed.Options.PlaceholderSeparateMenu')
        Publisher.subscribe(self.on_settings_loaded, 'settings.loaded')
        Publisher.subscribe(self.on_open_wallpaper_dialog, 'wallpaper.open_dialog')
        Publisher.subscribe(self.on_open_options_dialog, 'options.open_dialog')
        Publisher.subscribe(self.on_open_movefile_dialog, 'movefile.open_dialog')
        Publisher.subscribe(self.on_open_debug_cache_dialog, 'debug.open_cache_dialog')
        Publisher.subscribe(self.on_open_about_dialog, 'about.open_dialog')
        Publisher.subscribe(self.on_open_directory_dialog, 'file_list.open_directory_dialog')
        Publisher.subscribe(self.on_update_available, 'program.update_available')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.loaded')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackground')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackgroundColor')

    def _bind_panel_mouse_events(self):
        def make_fn(btn_idx, evt_idx):
            def fn(evt):
                Publisher.sendMessage('canvas.mouse.event', button=btn_idx, event=evt_idx, x=evt.x, y=evt.y)
                evt.Skip()
            return fn
        for button_idx, button in enumerate(('LEFT', 'MIDDLE', 'RIGHT', 'MOUSE_AUX1', 'MOUSE_AUX2')):
            for event_idx, event in enumerate(('DOWN', 'UP')):
                eid = getattr(wx, f'EVT_{button}_{event}')
                self.panel.Bind(eid, make_fn(button_idx, event_idx))
    
    @property
    def canvas_view(self):
        return CanvasAdapter(self.panel)
    
    def save(self, settings_lst):
        perspective = self.aui_mgr.SavePerspective()
        settings_lst.append(('Window', 'Perspective', perspective))
        settings_lst.append(('Window', 'MainWindowX', self._last_pos[0]))
        settings_lst.append(('Window', 'MainWindowY', self._last_pos[1]))
        settings_lst.append(('Window', 'MainWindowWidth', self._last_size[0]))
        settings_lst.append(('Window', 'MainWindowHeight', self._last_size[1]))
        settings_lst.append(('Window', 'MainWindowMaximized', '1' if self.IsMaximized() else '0'))
        settings_lst.append(('Window', 'MainWindowFullscreen', '1' if self.IsFullScreen() else '0'))
    
    def load(self, settings: Settings):
        perspective = settings.get('Window', 'Perspective')
        if perspective:
            self.aui_mgr.LoadPerspective(perspective)
        width = max(settings.getint('Window', 'MainWindowWidth'), 200)
        height = max(settings.getint('Window', 'MainWindowHeight'), 200)
        x = max(settings.getint('Window', 'MainWindowX'), 0)
        y = max(settings.getint('Window', 'MainWindowY'), 0)
        self.set_window_size(x, y, width, height)
        self.Maximize(settings.getboolean('Window', 'MainWindowMaximized'))
        if wx.Display.GetFromWindow(self) == wx.NOT_FOUND:
            self.SetSize(0, 0, width, height)

    def on_resize(self, event: wx.SizeEvent):
        Publisher.sendMessage('canvas.resized')
        if not self.IsMaximized() and not self.IsFullScreen():
            self._last_size = self.get_window_size()
            
    def on_move(self, event: wx.MoveEvent):
        if not self.IsMaximized() and not self.IsFullScreen():
            self._last_pos = self.GetPosition()

    def get_window_size(self):
        """Calls either wx.GetSize or wx.GetClientSize. GetSize has better results on Windows, Client on Linux
        (or at least Wayland; maybe X11 works differently). If the wrong function is used the save&restore logic
        may end up growing the window each time the application is opened and closed."""
        if sys.platform == 'win32':
            return self.GetSize()
        else:
            return self.GetClientSize()
    def set_window_size(self, x:int, y: int, w: int, h: int):
        """As with get. The parameters are different so this is two calls on Linux."""
        if sys.platform == 'win32':
            self.SetSize(x, y, w, h)
        else:
            self.SetClientSize(w, h)
            self.SetPosition(wx.Point(x, y))

    @error_handler(_handle_error)
    def on_close(self, event: wx.CloseEvent):
        settings_lst: Any = []
        self.save(settings_lst)
        self.file_list_panel.save(settings_lst)
        try:
            Publisher.sendMessage('program.closed', settings_lst=settings_lst)
        except Exception:
            log.error(traceback.format_exc())
        
        self.aui_mgr.UnInit()
        del self.aui_mgr
        self.Destroy()
        
    def on_mouse_motion(self, event: wx.MouseEvent):
        Publisher.sendMessage('canvas.mouse.motion', x=event.GetX(), y=event.GetY())
        event.Skip()
        
    def on_settings_loaded(self, *, settings: Settings):
        self.load(settings)
        self.file_list_panel.load(settings)
    
    def on_panel_paint(self, event: wx.PaintEvent):
        dc: wx.DC
        if meta.DOUBLE_BUFFERING:
            dc = wx.BufferedPaintDC(self.panel)
            dc.Clear()
        else:
            dc = wx.PaintDC(self.panel)
        #This is required on Linux
        dc.SetBackground(wx.Brush(self.panel.GetBackgroundColour()))
        painted_region = PaintedRegion()
        #The recipient will update the painted_region fields.
        Publisher.sendMessage('canvas.painted', dc=dc, painted_region=painted_region)
        size = self.panel.GetSize()
        clip_region = wx.Region(0, 0, size[0], size[1])
        clip_region.Subtract(wx.Rect(painted_region.left, painted_region.top,
                                     painted_region.width, painted_region.height))
        #Fix for bug in Linux (without this it would clear the entire image
        #when the panel is smaller than the image
        
        if not meta.DOUBLE_BUFFERING:
            itr = wx.RegionIterator(clip_region)
            while (itr.HaveRects()):
                rect = itr.GetRect()
                dc.DestroyClippingRegion()
                dc.SetClippingRegion(rect)
                dc.Clear()
                itr.Next()
        
    def on_mouse_wheel(self, event: wx.MouseEvent):
        lines = event.GetWheelRotation() / event.GetWheelDelta()
        lines *= event.GetLinesPerAction()
        if event.controlDown:
            #Zoom instead of scrolling
            Publisher.sendMessage('canvas.zoom_at', lines=lines, x=event.X, y=event.Y)
        else:
            Publisher.sendMessage('canvas.scrolled', lines=lines, horizontal=event.shiftDown)
        
    def on_mouse_enter(self, event: wx.MouseEvent):
        self.panel.SetFocus()
        
    def on_fit_context_menu(self, event: wx.ContextMenuEvent):
        """Appears on right-clicking the status bar"""
        self.PopupMenu(self.menus[MenuName.FitCtx])
        
    def on_cmd_context_menu(self):
        """Appears on executing the bindable 'open context menu' command, e.g. middle/right clicking. """
        self.PopupMenu(self.menus[MenuName.ImgCtx])
        
    def on_busy(self, *, busy):
        if self._busy == busy:
            return
        if busy:
            wx.BeginBusyCursor()
        else:
            #Fix for a bizarre bug that would deadlock the app on Linux
            wx.CallAfter(wx.EndBusyCursor)
        self._busy = busy
        
    def on_freeze(self):
        self.Freeze()
        
    def on_thaw(self):
        self.Thaw()
    
    def on_error(self, *, exception, tb):
        self.handle_error(exception, tb)
        
    def on_canvas_changed(self):
        self.panel.Refresh(eraseBackground=False)

    def on_canvas_fit_changed(self, *, FitType, IsSpread=False):
        fit_choices = get_fit_choices()
        name = [name for name, typ in fit_choices if typ == FitType][0]
        txt = name
        if IsSpread:
            txt += ' ' + _('(Spread)')
        self.status_bar.SetStatusText(txt, FIT_FIELD)

    def on_canvas_cursor_changed(self, *, cursor):
        self.panel.SetCursor(cursor)
        
    def on_canvas_zoom_changed(self, *, zoom):
        text = util.get_formatted_zoom(zoom)
        self.status_bar.SetStatusText(text, ZOOM_FIELD)
        
    def on_menu_built(self, *, main_menu: list[MenuName], all_menus: list[CommandCategory], commands: list[Command]):
        """ Turn the model objects into actual wx menu objects and store them locally.
        These will be used to populate the menu bar (immediately) and context menus (on demand)
        :param main_menu: The menus that should appear in the menubar. The associated category object will be modified to include the index.
        :param all_menus: All CommandCategory objects (derived from the MenuDefinition). Order matters as menus may reference previous menus.
        :param commands: All command objects
        """
        menu_lookup = {x.idx: x for x in all_menus}
        cmd_lookup = {x.ide: x for x in commands if type(x) is Command}
        #This function should only be called once. But if it is called multiple times, reset state.
        self.all_cmd_pairs = []
        #First, create the wx.Menu objects. This is done for everything. Populate self.menus
        for item in all_menus:
            #make_menu will also modify all_cmd_pairs
            wx_menu = self.make_menu(item, menu_lookup, cmd_lookup)
            self.menus[item.idx] = wx_menu
            self.menu_names[item.idx] = item.name
        
        #Add the appropriate items to self.menu_bar (use Append). Set indices
        i = 0
        for idx in main_menu:
            menu = self.menus[idx]
            category = menu_lookup[idx]
            self.menu_bar.Append(menu, category.name)
            #Need to manually track the id. Searching by name doesn't work if the name can change (translations)
            #Just counting up is fine as long as there aren't existing menu items, and there shouldn't be.
            category.menu_idx = i
            i += 1

        #Create actual bindings for the commands
        for command in commands:
            def event_fn(event, cmd=command):
                try:
                    cmd()
                except Exception as e:
                    self.handle_error(e)
            self.Bind(wx.EVT_MENU, event_fn, id=command.ide)
        #This is the number of pre-defined menu items in favorites; everything past this is a favorite.
        self._favorite_menu_count = self.menus[MenuName.Favorites].GetMenuItemCount()

    def make_menu(self, menu: CommandCategory, all_menus: dict[MenuName, CommandCategory], cmd_lookup: dict[int, Command]) -> wx.Menu:
        """ Creates the actual wx.Menu for a given CommandCategory.
        Still requires references to all data, since this may include submenus.
        """
        _menu = wx.Menu()
        for cmd in menu.commands:
            if cmd is None:
                _menu.AppendSeparator()
            # Submenu
            elif type(cmd) is MenuName:
                if cmd not in self.menus:
                    raise Exception(f"Menu {cmd} referenced before it was created.")
                submenu = self.menus[cmd]
                data = all_menus[cmd]
                _menu.AppendSubMenu(submenu, data.name)
            # Command
            elif type(cmd) is CommandName:
                command = cmd_lookup[cmd]
                style = wx.ITEM_CHECK if command.checkable else wx.ITEM_NORMAL
                wx_menuitem = _menu.Append(command.ide, command.name_and_shortcut, command.description, style)
                #Track for later updates (i.e. translations).
                self.all_cmd_pairs.append((command, wx_menuitem))
                #If a cmd is in multiple menus, it will bind multiple times. Is this a problem?
                if command.update_function:
                    wx.GetApp().Bind(wx.EVT_UPDATE_UI, command.update_function, id=command.ide)
        return _menu

    def _reset_favorite_menus(self):
        """The favorites menus are always updated by wiping them out and re-building from scratch.
        Call this within a 'freeze' block. """
        favorites_menu = self.menus[MenuName.Favorites]

        reset_submenus = (self.menus[MenuName.FavoritesSub], self.menus[MenuName.PlaceholderSub], self.menus[MenuName.FavoritesCtx], self.menus[MenuName.PlaceholderCtx])
        for menu in reset_submenus:
            while menu.GetMenuItemCount() > 0:
                item = menu.FindItemByPosition(0)
                menu.Delete(item)
        # self._favorite_menu_count is the number of submenus in the favorites menu;
        #      entries bigger than this are the favorites themselves.
        while favorites_menu.GetMenuItemCount() > self._favorite_menu_count:
            item = favorites_menu.FindItemByPosition(self._favorite_menu_count)
            favorites_menu.Delete(item)
    def on_favorite_settings_changed(self, settings: Settings):
        """Updates the various menus that display favorites. Called when settings change or when the favorites change."""
        #The best way to handle this is likely to alternate between adding favorites directly to the menu and the two sub menus.
        #Trying to do this is giving me wx free errors.
        pass
    def _create_favorites(self, favorites: Favorites):
        """Resets and populates self.favorites_menu_items"""
        items = favorites.getitems()
        self.favorites_menu_items = []
        i = 0
        for path_key, fav in items:
            ide = wx.NewId()
            def event_fn(event: wx.CommandEvent, favorite=fav):
                try:
                    Publisher.sendMessage('favorite.open', favorite=favorite, window=self)
                except Exception as e:
                    self.handle_error(e)

            name = fav.displayText()
            if not name:
                continue

            self.favorites_menu_items.append(FavoriteMenuItem(ide, name, fav))
            self.Bind(wx.EVT_MENU, event_fn, id=ide)
            i += 1
    def on_favorites_changed(self, *, favorites: Favorites, settings: Settings):
        favorites_menu = self.menus[MenuName.Favorites]
        fav_only = self.menus[MenuName.FavoritesSub]
        fav_ctx = self.menus[MenuName.FavoritesCtx]
        place_only = self.menus[MenuName.PlaceholderSub]
        place_ctx = self.menus[MenuName.PlaceholderCtx]
        self._create_favorites(favorites)
        self.menu_bar.Freeze()
        try:
            self._reset_favorite_menus()
            #Rebuild
            if self.favorites_menu_items:
                favorites_menu.AppendSeparator()
            for item in self.favorites_menu_items:
                favorites_menu.Append(item.ide, item.name)
                if item.fav.is_placeholder():
                    place_only.Append(item.ide, item.name)
                    place_ctx.Append(item.ide, item.name)
                else:
                    fav_only.Append(item.ide, item.name)
                    fav_ctx.Append(item.ide, item.name)
        finally:
            self.menu_bar.Thaw()
        pass

    def on_shortcuts_changed(self, *, accel_table: wx.AcceleratorTable):
        self.accel_table = accel_table
        self.SetAcceleratorTable(self.accel_table)

    def on_menu_labels_changed(self, *, categories: list[CommandCategory]):
        #Commands (i.e. wx.MenuItem s) use stored data. The menu_bar requires indices; wx.Menu references will not work.
        for (cmd, wx_item) in self.all_cmd_pairs:
            wx_item.SetItemLabel(cmd.name)
            wx_item.SetHelp(cmd.description)
        for category in categories:
            #Need to use the idx stored in the category (when the bar is created)
            #Finding by name isn't reliable if the name can change.
            midx = category.menu_idx
            if midx != -1:
                self.menu_bar.SetMenuLabel(midx, category.name)
    
    def on_container_opened(self, *, container: BaseContainer):
        self.SetTitle(f'{container.name} - {meta.APPNAME}')
        self.status_bar.SetStatusText(container.name, NAME_FIELD)
    
    def on_image_opened(self, *, item):
        self.SetTitle(f'{item.name} - {meta.APPNAME}')
        self.status_bar.SetStatusText(str(item.full_path), NAME_FIELD)
        
    def on_image_loading(self, *, item):
        self.status_bar.SetStatusText(_('Loading...'), NAME_FIELD)
        
    def on_image_loaded(self, *, img):
        if img is None:
            self.status_bar.SetStatusText('', SIZE_FIELD)
            self.status_bar.SetStatusText('', ZOOM_FIELD)
        else:
            width = img.original_width
            height = img.original_height
            self.status_bar.SetStatusText('%d x %d' % (width, height), SIZE_FIELD)

    def on_language_changed(self):
        self.aui_mgr.GetPane('file_list').Caption(_('Files'))
        self.aui_mgr.Update()
        if self.update_menu_item:
            self.update_menu_item.SetItemLabel(_('&Download'))
            self.update_menu_item.SetHelp(_('Go to the download site'))
            self.menu_bar.SetMenuLabel(self.menu_bar.GetMenuCount()-1,
                                       _('&New version available!'))
    
    def on_open_wallpaper_dialog(self, *, choices, color):
        from quivilib.gui.wallpaper import WallpaperDialog
        dialog = WallpaperDialog(self, choices, color)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_open_options_dialog(self, *, fit_choices, settings, commands, available_languages, active_language, save_locally):
        from quivilib.gui.options import OptionsDialog
        dialog = OptionsDialog(self, fit_choices, settings, commands, available_languages, active_language, save_locally)
        dialog.ShowModal()
        dialog.Destroy()
    
    def on_open_movefile_dialog(self, *, settings: Settings, name='', start_path=''):
        from quivilib.gui.move_file import MoveFileDialog
        dialog = MoveFileDialog(self, settings, name=name, start_path=start_path)
        if dialog.ShowModal() == wx.ID_OK:
            target_path = dialog.GetPath()
            Publisher.sendMessage('file_list.move_file', new_dir=target_path)
        dialog.Destroy()
        
    def on_open_debug_cache_dialog(self, *, params):
        if __debug__:
            self.dbg_dialog.Show()       #Modeless
            #dialog.Destroy()
        #Do nothing in a release build
        
    def on_open_directory_dialog(self, *, req):
        dialog = wx.DirDialog(self, _('Choose a directory:'),
                              style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
        dialog.SetPath(str(req.start_directory))
        if dialog.ShowModal() == wx.ID_OK:
            req.directory = Path(dialog.GetPath())
        dialog.Destroy()
        
    def on_open_about_dialog(self):
        from quivilib.gui.about import AboutDialog
        dialog = AboutDialog(self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_update_available(self, *, down_url, check_time, version):
        self.down_url = down_url
        menu = self.menus[MenuName.Downloads]
        menu_idx = self.menu_bar.GetMenuCount()
        self.menu_bar.Append(menu, self.menu_names[MenuName.Downloads])
        Publisher.sendMessage('menu.item_added', cmd=MenuName.Downloads, idx=menu_idx)

    def on_download_update(self):
        Publisher.sendMessage('program.open_update_site', url=self.down_url)

    def on_bg_color_changed(self, *, settings: Settings):
        if settings.get('Options', 'CustomBackground') == '1':
            color = settings.get('Options', 'CustomBackgroundColor').split(',')
            color = wx.Colour(*[int(c) for c in color])
        else:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE)
        self.panel.SetBackgroundColour(color)
        self.panel.Refresh()

    def handle_error(self, exception, tb=None):
        from quivilib.gui.error import ErrorDialog
        if not tb:
            tb = traceback.format_exc()
        msg, tb = util.format_exception(exception, tb)
        log.error(tb)
        print(tb)##
        def fn():
            dlg = ErrorDialog(parent=self, error=msg, tb=tb)
            dlg.ShowModal()
            dlg.Destroy()
        #TODO: (2,?) Investigate
        #This is a workaround for a bizarre bug in wx.
        wx.CallLater(400, fn)

    
    class QuiviFileDropTarget(wx.FileDropTarget):
        def __init__(self, window):
            self.Window = window
            wx.FileDropTarget.__init__(self)

        @error_handler(_handle_error)
        def OnDropFiles(self, x, y, filenames):
            filename = filenames[0]
            path = Path(filename)
            Publisher.sendMessage('file.dropped', path=path)
            return True
        
        def handle_error(self, exception):
            self.Window.handle_error(exception)
            return False
