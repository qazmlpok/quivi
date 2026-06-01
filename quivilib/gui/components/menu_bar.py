import wx
import wx.aui
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model import Favorites
from quivilib.model.command import Command, CommandCategory
from quivilib.model.commandenum import MenuName, CommandName
from quivilib.model.favorites import FavoriteMenuItem
from quivilib.model.settings import Settings


class QuiviMenuBar(wx.MenuBar):
    def __init__(self, style = 0):
        super().__init__(style)

        #List of (id, name) tuples. Filled on the favorites.changed event,
        #used in the file list popup menu
        self.favorites_menu_items: list[FavoriteMenuItem] = []
        self._favorite_menu_count = 0
        self.update_menu_item = None
        #Track as a dictionary
        self.menus: dict[MenuName, wx.Menu] = {}
        self.menu_names: dict[MenuName, str] = {}
        #Used for updating translations dynamically. Pair the actual wx objects and the local definitions.
        self.all_cmd_pairs: list[tuple[Command, wx.MenuItem]] = []

        self.accel_table = None

        # Set by a background task if there is an update available.
        self.down_url: str | None = None

        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_menu_built, 'menu.built')
        Publisher.subscribe(self.on_menu_labels_changed, 'menu.labels.changed')
        Publisher.subscribe(self.on_favorites_changed, 'favorites.changed')
        Publisher.subscribe(self.on_update_available, 'program.update_available')
        # Publisher.subscribe(self.on_favorite_settings_changed, 'settings.changed.Options.PlaceholderSeparateMenu')

    def on_menu_built(self, *, main_menu: list[MenuName], all_menus: list[CommandCategory], commands: list[Command]):
        """ Turn the model objects into actual wx menu objects and store them locally.
        These will be used to populate the menu bar (immediately) and context menus (on demand)
        :param main_menu: The menus that should appear in the menubar. The associated category object will be modified to include the index.
        :param all_menus: All CommandCategory objects (derived from the MenuDefinition). Order matters as menus may reference previous menus.
        :param commands: All command objects
        """
        menu_lookup = {x.idx: x for x in all_menus}
        cmd_lookup = {x.ide: x for x in commands if type(x) is Command}
        # This function should only be called once. But if it is called multiple times, reset state.
        self.all_cmd_pairs = []
        # First, create the wx.Menu objects. This is done for everything. Populate self.menus
        for item in all_menus:
            # make_menu will also modify all_cmd_pairs
            wx_menu = self.make_menu(item, menu_lookup, cmd_lookup)
            self.menus[item.idx] = wx_menu
            self.menu_names[item.idx] = item.name

        # Add the appropriate items to self (use Append). Set indices
        i = 0
        for idx in main_menu:
            menu = self.menus[idx]
            category = menu_lookup[idx]
            self.Append(menu, category.name)
            # Need to manually track the id. Searching by name doesn't work if the name can change (translations)
            # Just counting up is fine as long as there aren't existing menu items, and there shouldn't be.
            category.menu_idx = i
            i += 1

        # This is the number of pre-defined menu items in favorites; everything past this is a favorite.
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

    def on_favorites_changed(self, *, favorites: Favorites, settings: Settings):
        favorites_menu = self.menus[MenuName.Favorites]
        fav_only = self.menus[MenuName.FavoritesSub]
        fav_ctx = self.menus[MenuName.FavoritesCtx]
        place_only = self.menus[MenuName.PlaceholderSub]
        place_ctx = self.menus[MenuName.PlaceholderCtx]
        self._create_favorites(favorites)
        self.Freeze()
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
            self.Thaw()
        pass

    def _create_favorites(self, favorites: Favorites):
        """Resets and populates self.favorites_menu_items"""
        items = favorites.getitems()
        self.favorites_menu_items = []
        Publisher.sendMessage("menu.reset_favorites")
        for path_key, fav in items:
            #TODO: Try to preserve IDs instead of creating new ones for old favorites.
            ide = wx.NewId()

            name = fav.displayText()
            if not name:
                continue

            self.favorites_menu_items.append(FavoriteMenuItem(ide, name, fav))
            Publisher.sendMessage("menu.bind_favorite", ide=ide, fav=fav)

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
                self.SetMenuLabel(midx, category.name)

    # Update available menu
    def on_language_changed(self):
        if self.update_menu_item:
            self.update_menu_item.SetItemLabel(_('&Download'))
            self.update_menu_item.SetHelp(_('Go to the download site'))
            self.SetMenuLabel(self.GetMenuCount()-1, _('&New version available!'))

    def on_update_available(self, *, down_url, check_time, version):
        self.down_url = down_url
        menu = self.menus[MenuName.Downloads]
        menu_idx = self.GetMenuCount()
        self.Append(menu, self.menu_names[MenuName.Downloads])
        Publisher.sendMessage('menu.item_added', cmd=MenuName.Downloads, idx=menu_idx)

    def do_download_update(self):
        Publisher.sendMessage('program.open_update_site', url=self.down_url)

    # Accessors for specific context menus
    def open_fit_menu(self):
        self.PopupMenu(self.menus[MenuName.FitCtx])

    def open_context_menu(self):
        self.PopupMenu(self.menus[MenuName.ImgCtx])
