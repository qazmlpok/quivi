from enum import IntEnum, Flag
import wx

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut

class CommandName(IntEnum):
    """ Unique identifiers for all menu commands.
    """
    #file_menu
    SET_WALLPAPER = 11001
    COPY = 11002
    COPY_PATH = 11005
    DELETE = 11004
    MOVE = 11006
    OPTIONS = 11003
    QUIT = wx.ID_EXIT

    #folder_menu
    SELECT_NEXT = 12001
    SELECT_PREVIOUS = 12002
    OPEN_SELECTED_DIRECTORY = 12003
    OPEN_PARENT = 12004
    OPEN_NEXT  = 12005
    OPEN_PREVIOUS  = 12006
    REFRESH = 12007
    OPEN_DIRECTORY = 12008

    #view_menu
    ZOOM_IN = 13001
    ZOOM_OUT = 13002
    ZOOM_FULL = 13003
    FIT_WIDTH = 13004
    FIT_HEIGHT = 13005
    SHOW_SPREAD = 13040
    ROTATE_CLOCKWISE = 13008
    ROTATE_COUNTER_CLOCKWISE = 13009
    FULL_SCREEN = 13006
    SHOW_FILE_LIST = 13007
    SHOW_THUMBNAILS = 13011
    SHOW_HIDDEN_FILES = 13010

    #favorites_menu
    ADD_FAVORITES = 14001
    ADD_PLACEHOLDER = 14003
    REMOVE_FAVORITES = 14002
    REMOVE_PLACEHOLDER = 14004

    #favorites_hidden_menu
    OPEN_LAST_PLACEHOLDER = 14005

    #help_menu
    HELP = 15001
    FEEDBACK = 15002
    ABOUT = wx.ID_ABOUT

    #hidden_menu
    MOVE_SMALL_UP = 16001
    MOVE_SMALL_DOWN = 16002
    MOVE_SMALL_LEFT = 16003
    MOVE_SMALL_RIGHT = 16004
    MOVE_LARGE_UP = 16005
    MOVE_LARGE_DOWN = 16006
    MOVE_LARGE_LEFT = 16007
    MOVE_LARGE_RIGHT = 16008
    MOVE_FULL_UP = 16009
    MOVE_FULL_DOWN = 16010
    MOVE_FULL_LEFT = 16011
    MOVE_FULL_RIGHT = 16012
    DRAG_IMAGE = 16100

    #fit_menu
    NONE = 17001
    WIDTH = 17002
    HEIGHT = 17003
    WINDOW = 17004
    WIDTH_LARGER = 17005
    HEIGHT_LARGER = 17006
    WINDOW_LARGER = 17007
    CUSTOM_WIDTH = 17008
    
    #debug
    CACHE_INFO = 29900
#

class CommandDefinition():
    """ Definition of a menu command. The unique id and name, but not any of the associated functions.
    The name and description are the translation key, but are not translated. This is to allow language switching.
    """
    def __init__(self, uid: int, nameKey: str, descrKey: str, shortcuts: list[tuple[wx.AcceleratorEntryFlags, wx.KeyCode|int]], flags=None, checkable=False):
        self.uid = uid
        self.nameKey = nameKey
        self.descrKey = descrKey
        self.shortcuts = [Shortcut(*x) for x in shortcuts]
        self.flags = flags
        self.checkable = checkable
    def __repr__(self):
        return f"CommandDef: {self.nameKey}"
#
class CommandDefinitionList():
    """ The list of all Command Definitions. Actually stored as a dict.
    """

    def __init__(self):
        listItems = [
            #file_menu
            CommandDefinition(CommandName.SET_WALLPAPER            , 'Set as &wallpaper...', 'Set the opened image as wallpaper', [(wx.ACCEL_NORMAL, wx.WXK_F3)]),
            CommandDefinition(CommandName.COPY                     , '&Copy', 'Copy the opened image to the clipboard',[(wx.ACCEL_CTRL, ord('C'))]),
            CommandDefinition(CommandName.COPY_PATH                , '&Copy path', 'Copy the path of the current container to the clipboard',[(wx.ACCEL_CTRL, ord('B'))]),
            CommandDefinition(CommandName.DELETE                   , '&Delete', 'Delete the opened image',[(wx.ACCEL_CTRL, wx.WXK_DELETE)], checkable=False),
            CommandDefinition(CommandName.MOVE                     , '&Move...', 'Move the opened zip file to a new location',[(wx.ACCEL_CTRL, ord('N'))], checkable=False),
            CommandDefinition(CommandName.OPTIONS                  , '&Options...', 'Open the options dialog',[(wx.ACCEL_NORMAL, wx.WXK_F4)]),
            CommandDefinition(CommandName.QUIT                     , '&Quit', 'Close the application',[], flags=Command.KB),
            
            #folder_menu
            CommandDefinition(CommandName.SELECT_NEXT              , 'Select/Open &next', 'Select the next item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_END), (wx.ACCEL_NORMAL, wx.WXK_SPACE)]),
            CommandDefinition(CommandName.SELECT_PREVIOUS          , 'Select/Open &previous', 'Select the previous item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_HOME)]),
            CommandDefinition(CommandName.OPEN_SELECTED_DIRECTORY  , 'Open selected &directory', 'If a directory or a compressed file is selected, open it',[(wx.ACCEL_NORMAL, wx.WXK_INSERT)]),
            CommandDefinition(CommandName.OPEN_PARENT              , 'Open p&arent', 'Open the parent directory or compressed file',[(wx.ACCEL_NORMAL, wx.WXK_DELETE)]),
            CommandDefinition(CommandName.OPEN_NEXT                , 'Open ne&xt sibling', 'Open the next directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_END)]),
            CommandDefinition(CommandName.OPEN_PREVIOUS            , 'Open previou&s sibling', 'Open the previous directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_HOME)]),
            CommandDefinition(CommandName.REFRESH                  , '&Refresh', 'Refresh the current directory or compressed file; reload the image shown if any',[(wx.ACCEL_NORMAL, wx.WXK_F5)]),
            CommandDefinition(CommandName.OPEN_DIRECTORY           , 'Open direc&tory...', 'Browse for a directory to open',[(wx.ACCEL_CTRL, ord('O'))]),

            #view_menu
            CommandDefinition(CommandName.ZOOM_IN                  , 'Zoom &in', 'Zoom in',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ADD)]),
            CommandDefinition(CommandName.ZOOM_OUT                 , 'Zoom &out', 'Zoom out',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_SUBTRACT)]),
            CommandDefinition(CommandName.ZOOM_FULL                , '&Zoom 100%', 'Show the image in its real size',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY)]),
            CommandDefinition(CommandName.FIT_WIDTH                , 'Fit &width', 'Zooms the image in order to make its width fit the window',[(wx.ACCEL_CTRL, ord('W'))]),
            CommandDefinition(CommandName.FIT_HEIGHT               , 'Fit &height', 'Zooms the image in order to make its height fit the window',[(wx.ACCEL_CTRL, ord('H'))]),
            CommandDefinition(CommandName.SHOW_SPREAD              , 'Show &spread', 'Attempt to show combined pages at regular zoom',[(wx.ACCEL_CTRL, ord('E'))], checkable=True),
            CommandDefinition(CommandName.ROTATE_CLOCKWISE         , 'Rotate &clockwise', 'Rotate the image clockwise',[(wx.ACCEL_CTRL, ord('L'))]),
            CommandDefinition(CommandName.ROTATE_COUNTER_CLOCKWISE , 'Rotate coun&ter clockwise', 'Rotate the image counter clockwise',[(wx.ACCEL_CTRL, ord('K'))]),
            CommandDefinition(CommandName.FULL_SCREEN              , '&Full screen', 'Go to/leave full screen mode',[(wx.ACCEL_ALT, wx.WXK_RETURN)], checkable=True),
            CommandDefinition(CommandName.SHOW_FILE_LIST           , 'File &list', 'Show/hide the file list',[(wx.ACCEL_NORMAL, wx.WXK_TAB)], checkable=True),
            CommandDefinition(CommandName.SHOW_THUMBNAILS          , 'Thumb&nails', 'Show/hide the thumbnails',[(wx.ACCEL_NORMAL, wx.WXK_F6)], checkable=True),
            CommandDefinition(CommandName.SHOW_HIDDEN_FILES        , 'Hi&dden files', 'Show/hide hidden files in the file list',[(wx.ACCEL_CTRL, ord('A'))], checkable=True),
            
            #favorites_menu
            CommandDefinition(CommandName.ADD_FAVORITES            , 'Add to &favorites', 'Add the current directory or compressed file to the favorites', [(wx.ACCEL_CTRL, ord('D'))]),
            CommandDefinition(CommandName.ADD_PLACEHOLDER          , 'Add &placeholder', 'Add the current directory or compressed file to the favorites on the current image',[(wx.ACCEL_CTRL, ord('F'))]),
            CommandDefinition(CommandName.REMOVE_FAVORITES         , 'R&emove from favorites', 'Remove the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('R'))]),
            CommandDefinition(CommandName.REMOVE_PLACEHOLDER       , 'Remove p&laceholder', 'Remove the saved page for the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('V'))]),
            
            #favorites_hidden_menu
            CommandDefinition(CommandName.OPEN_LAST_PLACEHOLDER    , 'Open last placeholder', 'Open the most recently created placeholder',[(wx.ACCEL_CTRL, ord('L'))]),
            
            #help_menu
            CommandDefinition(CommandName.HELP                     , '&Help (online)...', 'Open the online help',[(wx.ACCEL_NORMAL, wx.WXK_F1)], flags=Command.KB),
            CommandDefinition(CommandName.FEEDBACK                 , '&Feedback / Support (online)...', 'Open the feedback / support online form',[], flags=Command.KB),
            CommandDefinition(CommandName.ABOUT                    , '&About...', 'Show information about the application',[], flags=Command.KB),
            
            #hidden_menu
            CommandDefinition(CommandName.MOVE_SMALL_UP            , 'Small move up', 'Small move up',[(wx.ACCEL_NORMAL, wx.WXK_UP)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_SMALL_DOWN          , 'Small move down', 'Small move down',[(wx.ACCEL_NORMAL, wx.WXK_DOWN)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_SMALL_LEFT          , 'Small move left', 'Small move left',[(wx.ACCEL_NORMAL, wx.WXK_LEFT)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_SMALL_RIGHT         , 'Small move right', 'Small move right',[(wx.ACCEL_NORMAL, wx.WXK_RIGHT)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_LARGE_UP            , 'Large move up', 'Large move up',[(wx.ACCEL_NORMAL, wx.WXK_PAGEUP)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_LARGE_DOWN          , 'Large move down', 'Large move down',[(wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN)], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_LARGE_LEFT          , 'Large move left', 'Large move left', [], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_LARGE_RIGHT         , 'Large move right', 'Large move right',[], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_FULL_UP             , 'Full move up', 'Full move up',[], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_FULL_DOWN           , 'Full move down', 'Full move down',[], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_FULL_LEFT           , 'Full move left', 'Full move left',[], flags=Command.KB),
            CommandDefinition(CommandName.MOVE_FULL_RIGHT          , 'Full move right', 'Full move right',[], flags=Command.KB),
            CommandDefinition(CommandName.DRAG_IMAGE               , 'Drag image', 'Drag image',[], flags=Command.MOUSE),
            
            #fit_menu
            CommandDefinition(CommandName.NONE                     , 'None', 'None',[]),
            CommandDefinition(CommandName.WIDTH                    , 'Width', 'Width',[]),
            CommandDefinition(CommandName.HEIGHT                   , 'Height', 'Height',[]),
            CommandDefinition(CommandName.WINDOW                   , 'Window', 'Window',[]),
            CommandDefinition(CommandName.WIDTH_LARGER             , 'Width if larger', 'Width if larger',[]),
            CommandDefinition(CommandName.HEIGHT_LARGER            , 'Height if larger', 'Height if larger',[]),
            CommandDefinition(CommandName.WINDOW_LARGER            , 'Window if larger', 'Window if larger',[]),
            CommandDefinition(CommandName.CUSTOM_WIDTH             , 'Custom width', 'Custom width',[]),

            #debug menu
            CommandDefinition(CommandName.CACHE_INFO               , 'Cache', 'Show Cache information',[]),
        ]
        self.commands = {x.uid: x for x in listItems}


class Command():
    (
        KB,         #Command can be assigned to a keyboard shortcut
        MOUSE,      #Command can be assigned to a mouse button
        NOMENU,     #Command does not appear in the application menu
    ) = (1 << x for x in range(3))
    KBM = KB|MOUSE

    def __init__(self, definition: CommandDefinition, function, 
            down_function=None, update_function=None):
        """
            Create a new command category.
            
            @param ide: Unique identifier for this command
            @param name: Display name for this command. Translated, will include &.
            @param description: Description for this command. Translated.
            @param function: Function to execute upon selecting this command.
            @param default_shortcuts: Default keyboard combination for this command
            @param flags: Flags for controlling where this command can be used, i.e. keyboard/mouse
            @param down_function: For mouse events, command to execute on mouse down
            @param checkable: If true, potentially show a checkmark in the menu (ref update_function)
            @param update_function: Function used to modify display of this menu item, e.g. to disable it or to check the checkbox.
        """
        self.ide = definition.uid
        self.name = definition.nameKey
        self.description = definition.descrKey
        self._function = function
        self._down_function = down_function
        self.default_shortcuts = definition.shortcuts
        self.shortcuts = []
        self.checkable = definition.checkable
        self.update_function = update_function
        self.flags = definition.flags
        if self.flags is None:
            self.flags = Command.KBM
        self.update_translation(definition)
    def update_translation(self, definition):
        #dumb hack to avoid translating the debug menu option stuff.
        if definition.uid < CommandName.CACHE_INFO:
            self.name = _(definition.nameKey)
            self.description = _(definition.descrKey)

    def load_default_shortcut(self):
        if self.default_shortcuts:
            self.shortcuts = self.default_shortcuts
        
    def __call__(self):
        self._function()
        
    def on_down(self):
        if self._down_function is not None:
            self._down_function()
        
    def __repr__(self):
        return f'{self.clean_name}: {self.description}'
        
    @property
    def name_and_shortcut(self):
        if self.shortcuts:
            return f'{self.name}\t{self.shortcuts[0].name}'
        else:
            return self.name
    
    @property
    def clean_name(self):
        return self.name.replace('&', '').replace('...', '')
#


class CommandCategory():
    def __init__(self, order: int, idx: str, name: str, commands: list[Command], hidden=False):
        """
            Create a new command category.
            
            @param order: The order within the Options menu (not used elsewhere)
            @param idx: string key to use as a unique identifier for this menu. Needed for updates.
            @param commands: Collection of commands (e.g. menu items) associated with this category.
            @param name: Display name for the menu - translated to the target language
            @param hidden: If true, the menu will be created but not added to the menu bar.
        """
        self.order = order
        self.idx = idx
        self.commands = commands
        self.name = name
        self.hidden = hidden
        
        #From what I'm seeing, the only way to find a menu is by the position or by the title.
        #Title poses problems when trying to update translations.
        #So to work around this, store the id when inserting the menu into the bar.
        self.menu_idx = -1
        
    @property
    def clean_name(self):
        return self.name.replace('&', '')
#
