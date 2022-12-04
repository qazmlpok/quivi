# Quivi
Quivi is an image viewer (specialized for comic/manga reading) which supports many file formats and compressed (zip, rar) files. It is aimed for fast & easy file browsing with keyboard or mouse. 
 
The home page for the original distribution of Quivi is http://quivi.sourceforge.net/

# Quivi-64
This fork was made with the primary purpose of adding 64-bit compatibility. The original Python code has been ported to Python 3.

# Added features
- Upgrading Python to version 3 fixed some Unicode issues
- Upgrading the image rendering libraries added support for webp
- Upgrading to 64-bit enables viewing very large images without crashing due to running out of memory
- Quivi will now remember if you closed the application while in fullscreen mode and automatically re-open in fullscreen mode. This can be disabled in the configuration ("Remember full screen on close")
- Added support for mouse auxiliary buttons (Aux1 and Aux2). These can be assigned behavior in the settings menu. By default they do nothing.
- Internal change to how the Config file (pyquivi.ini) is written to should reduce the chances of it becoming corrupted
- If the config file does become corrupt, it will re-create a new file from scratch instead of making the application inoperable.
- The config file is now stored as UTF-8 instead of the system default. It will attempt to open the file both as UTF-8 and the system default, but always write as UTF-8.
- New feature: Placeholders. These act like Favorites, but with some changes. The behavior can be tweaked in Settings.
    - Placeholders save a path and a specific page. They are intended to quickly resume reading something you're in the middle of.
    - Only one placeholder can exist for an item; saving a new placeholder will replace the existing one
    - (Optionally) Only a single place holder can be used for anything. Saving any new placeholder will replace the existing one.
    - (Optionally) Placeholders will be deleted upon opening
    - (Optionally) Opening a folder/archive that has a placeholder will automatically load the placeholder
- Holding down shift while using the scrollwheel will scroll horizontally.
- Holding down ctrl while using the scrollwheel zoom in/out on the mouse cursor's location (instead of the center of the image)

# Removed features
For the most part, existing functionality is being kept intact. A few things were dropped either due to difficulty porting the code from Python2 to Python3, or because they aren't needed any more.
- Support for mangafox and onemanga was removed. Neither site is still active. The relevant code could be repurposed for other website(s) with a public API, but I would rather focus on being an offline reader.
- *Embedded* RAR support was removed. RAR files can still be opened as long as winrar is installed. 
- Internally, GDI and Cairo are no longer supported. These were only used to speed up image display. I was not able to get Cairo to work at all; GDI works except for webp. The speed difference between using GDI and not was negligible, so it has been disabled.

# Porting progress
Most of the 2 -> 3 conversion was automatic, which did leave some artifacts that need to be cleaned up. It's also likely there's some real division that needs to be corrected. Some of the Unicode hacks were removed, but others may remain. Python3 should give much better Unicode support overall.

- Updated to support Python 3.10.6
- wx updated to 4.2.0
- wx.lib.pubsub was split off of Wx as Pypubsub; version 4.0.3 is used.
- Image display supports GDI, Freeimage, and PIL (Pillow) works. Cairo is not supported.
- Removed online manga reader support. This is mostly to simplify the conversion process, as it allowed dropping httplib and beautifulsoup from the project
- Removed third party path utlity; pathlib (core Python module) is used instead.
- Only minimal testing has been done in Linux. The console logs numerous warnings about key accelerators, but for the most part the app works (tested in Ubuntu)
- Tests haven't been modified, except for the automated conversion

# Missing translations
The following text strings are new and have not been added to any of the translation files.

- Remember full screen on close
- Delete placeholders when opening
- Only allow a single placeholder
- Automatically jump to placeholder page on open
- Aux1 click
- Aux2 click
- Open last placeholder
- Open the most recently created placeholder
- Add &placeholder
- Remove p&laceholder
- Add the current directory or compressed file to the favorites on the current image
- Remove the saved page for the current directory or compressed file from the favorites
- The file or directory "%s" couldn't be found. Remove the favorite?
- Favorite not found
- The settings file is corrupt and cannot be opened. Settings will return to their default values. The corrupt file has been renamed to %s.
- The settings file is corrupt and cannot be opened. Settings will return to their default values.
- &Copy path
- Copy the path of the current container to the clipboard
- Drag Image
