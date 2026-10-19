import logging as log
import sys
import traceback
from pathlib import Path
from typing import Any

import wx
import wx.aui
from pubsub import pub as Publisher

from quivilib import meta
from quivilib import util
from quivilib.control.i18n import LanguageList
from quivilib.gui.components.QuiviViewPanel import QuiviViewPanel
from quivilib.gui.components.menu_bar import QuiviMenuBar
from quivilib.gui.components.status_bar import QuiviStatusBar
from quivilib.gui.debug_cache import DebugCacheDialog
from quivilib.gui.debug_memory import DebugMemoryDialog
from quivilib.gui.file_list import FileListPanel
from quivilib.i18n import _
from quivilib.interface.canvasadapter import CanvasAdapter
from quivilib.model.command import Command
from quivilib.model.commandenum import FitSettings
from quivilib.model.container import Item
from quivilib.model.container.base import BaseContainer
from quivilib.model.favorites import Favorite
from quivilib.model.settings import Settings
from quivilib.resources import images
from quivilib.util import error_handler


def _handle_error(exception, args, kwargs):
    self = args[0]
    return self.handle_error(exception)


class MainWindow(wx.Frame):
    """The main Window for Quivi"""
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1, title=meta.APPNAME)
        self.aui_mgr = wx.aui.AuiManager()
        self.aui_mgr.SetManagedWindow(self)
        self.aui_mgr.SetFlags(self.aui_mgr.GetFlags() & ~wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE)

        bundle = QuiviIconBundle()
        self.SetIcons(bundle)

        # Timer that runs every 1s and broadcasts. This allows non-frame components to access a timer for very simple stuff.
        self.global_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_global_timer, self.global_timer)
        self.global_timer.Start(1000)

        dt = self.QuiviFileDropTarget(self)
        self.SetDropTarget(dt)

        self.menu_bar = QuiviMenuBar()
        self.SetMenuBar(self.menu_bar)
        
        self.status_bar = QuiviStatusBar(self)
        self.SetStatusBar(self.status_bar)

        self.file_list_panel = FileListPanel(self)
        self.aui_mgr.AddPane(self.file_list_panel, wx.aui.AuiPaneInfo().
                             Name('file_list').Caption(_('Files')).Left().
                             Layer(1).Position(0).CloseButton(True).
                             DestroyOnClose(False).BestSize(300, 400))

        self.panel = QuiviViewPanel(self)
        self.aui_mgr.AddPane(self.panel, wx.aui.AuiPaneInfo().Name("content").CenterPane())
        
        self.aui_mgr.Update()
        self.bindings_and_subscriptions()

        if __debug__:
            #These are created immediately because they listen for messages.
            self.dbg_cache_dialog = DebugCacheDialog(self)
            self.dbg_memory_dialog = DebugMemoryDialog(self)

        self._last_size = self.get_window_size()
        self._last_pos = self.GetPosition()     # NOTE - This has no effect on Wayland
        self._busy = False

        self.accel_table = None
        self._bound_favorites: list[int] = []

    def bindings_and_subscriptions(self):
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
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_menu_built, 'menu.built')
        Publisher.subscribe(self.on_favorites_reset, 'menu.reset_favorites')
        Publisher.subscribe(self.on_favorite_bind, 'menu.bind_favorite')
        Publisher.subscribe(self.on_shortcuts_changed, 'menu.shortcuts.changed')
        Publisher.subscribe(self.on_cmd_context_menu, 'menu.context_menu')
        Publisher.subscribe(self.on_settings_loaded, 'settings.loaded')
        Publisher.subscribe(self.on_open_wallpaper_dialog, 'wallpaper.open_dialog')
        Publisher.subscribe(self.on_open_options_dialog, 'options.open_dialog')
        Publisher.subscribe(self.on_open_movefile_dialog, 'movefile.open_dialog')
        Publisher.subscribe(self.on_open_debug_cache_dialog, 'debug.open_cache_dialog')
        Publisher.subscribe(self.on_open_debug_memory_dialog, 'debug.open_memory_dialog')
        Publisher.subscribe(self.on_open_about_dialog, 'about.open_dialog')
        Publisher.subscribe(self.on_open_directory_dialog, 'file_list.open_directory_dialog')

    @property
    def canvas_view(self):
        return CanvasAdapter(self.panel)
    
    def save(self, settings_lst: list[tuple[str, str, str]]):
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
        # Necessary as of wxWidgets 3.3. May be needed in other locations.
        self.aui_mgr.Update()
            
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
    def set_window_size(self, x: int, y: int, w: int, h: int):
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

    def on_global_timer(self, event: wx.TimerEvent):
        Publisher.sendMessage("timer.pulse")

    def on_settings_loaded(self, *, settings: Settings):
        self.load(settings)
        self.file_list_panel.load(settings)

    def on_fit_context_menu(self, event: wx.ContextMenuEvent):
        """Appears on right-clicking the status bar"""
        # Note - on Windows, it appears to be necessary to call PopupMenu here, not in the menubar. Linux doesn't care.
        self.PopupMenu(self.menu_bar.get_fit_menu())
        
    def on_cmd_context_menu(self):
        """Appears on executing the bindable 'open context menu' command, e.g. middle/right clicking. """
        self.PopupMenu(self.menu_bar.get_context_menu())
        
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

    def on_menu_built(self, *, main_menu, all_menus, commands: list[Command]):
        """ Bind the functions for the menu commands.
        :param commands: All command objects
        """
        # Create actual bindings for the commands
        for command in commands:
            def event_fn(event, cmd=command):
                try:
                    cmd()
                except Exception as e:
                    self.handle_error(e)

            self.Bind(wx.EVT_MENU, event_fn, id=command.ide)

    def on_favorites_reset(self):
        """ Unbind all favorites and clear out the local cache.
        This isn't strictly necessary (the menus are destroyed) but it's probably a good idea."""
        for i in self._bound_favorites:
            self.Unbind(wx.EVT_MENU, id=i)
        self._bound_favorites = []

    def on_favorite_bind(self, *, ide: int, fav: Favorite):
        """ Bind a favorite"""

        def event_fn(event: wx.CommandEvent, favorite=fav):
            try:
                Publisher.sendMessage('favorite.open', favorite=favorite, window=self)
            except Exception as e:
                self.handle_error(e)

        self.Bind(wx.EVT_MENU, event_fn, id=ide)
        self._bound_favorites.append(ide)

    def on_shortcuts_changed(self, *, accel_table: wx.AcceleratorTable):
        self.accel_table = accel_table
        self.SetAcceleratorTable(self.accel_table)

    def on_container_opened(self, *, container: BaseContainer):
        self.SetTitle(f'{container.name} - {meta.APPNAME}')
    
    def on_image_opened(self, *, item: Item):
        self.SetTitle(f'{item.name} - {meta.APPNAME}')

    def on_language_changed(self):
        self.aui_mgr.GetPane('file_list').Caption(_('Files'))
        self.aui_mgr.Update()
    
    def on_open_wallpaper_dialog(self, *, choices: list[str], color: wx.Colour):
        from quivilib.gui.wallpaper import WallpaperDialog
        dialog = WallpaperDialog(self, choices, color)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_open_options_dialog(self, *, fit_choices: list[tuple[str, FitSettings.FitType]], settings: Settings, commands: list[Command], languages: LanguageList, save_locally: bool):
        from quivilib.gui.options.options import OptionsDialog
        dialog = OptionsDialog(self, fit_choices, settings, commands, languages, save_locally)
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
            self.dbg_cache_dialog.Show()       #Modeless
            #dialog.Destroy()
        #Do nothing in a release build
    def on_open_debug_memory_dialog(self, *, params):
        if __debug__:
            self.dbg_memory_dialog.Show()  # Modeless
            # dialog.Destroy()
        # Do nothing in a release build

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

    def do_download_update(self):
        self.menu_bar.do_download_update()

    def on_bg_color_changed(self, *, settings: Settings):
        self.panel.on_bg_color_changed(settings=settings)

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


class QuiviIconBundle(wx.IconBundle):
    """Icon bundle. Exists just to simplify the constructor a tiny bit."""
    def __init__(self):
        super().__init__()
        self.AddIcon(images.quivi16.Icon)
        self.AddIcon(images.quivi32.Icon)
        self.AddIcon(images.quivi48.Icon)
        self.AddIcon(images.quivi256.Icon)