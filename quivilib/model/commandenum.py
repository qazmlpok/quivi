from enum import IntEnum, StrEnum, IntFlag, Flag, auto
import wx

# Assorted enums associated with menu items. Also settings (which are closely related...)

class MovementType(Flag):
    MOVE = auto()
    MOVE_HORI = auto()
    MOVE_NEG = auto()
    
    MOVETYPE_SMALL = auto()
    MOVETYPE_LARGE = auto()
    MOVETYPE_FULL = auto()
    
    #Composite directions
    MOVE_LEFT = MOVE | MOVE_HORI
    MOVE_RIGHT = MOVE | MOVE_HORI | MOVE_NEG
    MOVE_UP = MOVE
    MOVE_DOWN = MOVE | MOVE_NEG


class FitSettings:
    #TODO: Proper enum.
    (FIT_NONE,
     FIT_WIDTH_OVERSIZE,
     FIT_HEIGHT_OVERSIZE,
     FIT_BOTH_OVERSIZE,
     FIT_CUSTOM_WIDTH,
     FIT_SCREEN_CROP_EXCESS,
     FIT_SCREEN_SHOW_ALL,
     FIT_SCREEN_NONE,
     FIT_TILED,
     FIT_WIDTH,
     FIT_HEIGHT,
     FIT_BOTH) = list(range(12))

class CommandFlags(IntFlag):
    NONE = 0
    KB = auto()          #Command can be assigned to a keyboard shortcut
    MOUSE = auto()       #Command can be assigned to a mouse button
    NOMENU = auto()      #Command does not appear in the application menu
    CHECKABLE = auto()   #Menu option can be shown as checked (requires an update function)
    DISABLEABLE = auto() #Menu option can be disabled (requires an update function)
    
    KBM = KB|MOUSE
    MASK = KB|MOUSE|NOMENU #Mask to ensure that at least one of these is set.
    
    #Using either CHECKABLE or DISABLEABLE requires that an update function is provided
    NEED_UPDATE = CHECKABLE | DISABLEABLE
#

class CommandName(IntEnum):
    """ Unique identifiers for all menu commands.
    wx.ID_HIGHEST = 5999. Don't use any value lower than this. Make sure everything is unique.
    """
    #file_menu
    SET_WALLPAPER = 11001
    COPY = 11002
    COPY_PATH = 11005
    DELETE = 11004
    DELETE_IMG = 11014
    DELETE_ZIP = 11024
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
    #This doesn't belong here but I'm thinking this "menu group" crap needs to go.
    OPEN_CONTEXT_MENU = 14006

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
    ZOOM_NONE = 17001
    ZOOM_WIDTH = 17002
    ZOOM_HEIGHT = 17003
    ZOOM_WINDOW = 17004
    ZOOM_WIDTH_LARGER = 17005
    ZOOM_HEIGHT_LARGER = 17006
    ZOOM_WINDOW_LARGER = 17007
    ZOOM_CUSTOM_WIDTH = 17008

    #download_menu
    DOWNLOAD_NEW = 18001
    
    #debug
    CACHE_INFO = 29900
    CHECK_UPDATE = 29901
    CLOSE_IMG = 29902
#

class MenuName(StrEnum):
    """ Unique identifiers for menus - both top-level (i.e. menubar) menus, 
    popup context menus, and sub-menus that can appear within another menu.
    """
    #Top level (menubar) menus
    File = 'file'
    Folder = 'fold'
    View = 'view'
    Favorites = 'fav'   #TODO: Ensure this can be a sub as well.
    Help = 'help'
    Downloads = 'download'      #Conditionally in the menu bar
    Debug = 'debug'     #Debug mode only
    #Top-level context menus
    FitCtx = '_fit'
    ImgCtx = '_ctx'
    #Sub menus
    ZoomSub = '_zoomSub'
    RotateSub = '_rotateSub'
    FavoritesSub = '_favoriteSub'       #Future; not implemented.
    PlaceholderSub = '_placeholderSub'  #Future; not implemented.
#
