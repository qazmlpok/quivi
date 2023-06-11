# Quivi
Quivi is an image viewer (specialized for comic/manga reading) which supports many file formats and compressed (zip, rar) files. It is aimed for fast & easy file browsing with keyboard or mouse. 
 
The home page for the original distribution of Quivi is http://quivi.sourceforge.net/

# Quivi-64
This fork was made with the primary purpose of adding 64-bit compatibility. The original Python code has been ported to Python 3.

# Added features
- Upgrading Python to version 3 fixed some Unicode issues.
- Upgrading the image rendering libraries added support for webp.
- Upgrading to 64-bit enables viewing very large images without crashing due to running out of memory.
- Quivi will now remember if you closed the application while in fullscreen mode and automatically re-open in fullscreen mode. This can be disabled in the configuration ("Remember full screen on close").
- Added support for mouse auxiliary buttons (Aux1 and Aux2). These can be assigned behavior in the settings menu. By default they do nothing.
- Internal change to how the Config file (pyquivi.ini) is written to should reduce the chances of it becoming corrupted.
- If the config file does become corrupt, it will re-create a new file from scratch instead of making the application inoperable.
- The config file is now stored as UTF-8 instead of the system default. It will attempt to open the file both as UTF-8 and the system default, but always write as UTF-8.
- New feature: Placeholders. These act like Favorites, but with some changes. The behavior can be tweaked in Settings.
    - Placeholders save a path and a specific page. They are intended to quickly resume reading something you're in the middle of.
    - Only one placeholder can exist for an item; saving a new placeholder will replace the existing one.
    - (Optionally) Only a single place holder can be used for anything. Saving any new placeholder will replace the existing one.
    - (Optionally) Placeholders will be deleted upon opening.
    - (Optionally) Opening a folder/archive that has a placeholder will automatically load the placeholder.
- Holding down shift while using the scrollwheel will scroll horizontally.
- Holding down ctrl while using the scrollwheel zoom in/out on the mouse cursor's location (instead of the center of the image).
- Added "Drag image" as an explicit command, instead of the default behavior of always dragging with left click. This means left click can be reassigned to a different action, such as Next image, and it will never attempt to move the image. The old behavior can be restored via an option in the Mouse tab.
    - Changed the default always drag behavior to have a threshold. If the mouse is moved more than x pixels, it is treated as a drag command. Otherwise it is a left button click (the other behavior was effectively a threshold of 0 pixels).
- Changed how the list of commands for keyboard/mouse are populated. Some commands are now marked as keyboard or mouse only. This technically removes functionality, but it makes the menu slightly easier to work with.
- Reworked how Cairo resizes image. If Cairo is enabled, images will be rescaled via a matrix operation instead of creating a new image. This is massively faster for the initial zoom, but slower for panning. The current approach is to use a high-quality resample while zooming, but a fast resample while panning. In the background, a high-quality resized image is created and used for panning when it is available. This is (roughly) the same approach taken by Eye of Gnome. It should be possible to always smoothing scale/pan at high quality, as GIMP does this, but I haven't figured it out.
- 16-bit precision images *should* work with PIL.
- Added option to view images right to left. Specifically, when opening an image that is larger than the screen, show the top-right corner of the image instead of the top-left corner. This has no effect if the Fit settings shrink the image to the size of the screen.
- New feature: Right-to-left viewing. When opening an image that is longer than the screen, start at the top-right corner instead of the top-left. This is for images that use a right-to-left reading order (i.e. Japanese manga). It will have no effect if the image is resized to the width of the viewer.
- New feature: Spread page viewing. If enabled and the current image is taller than it is long (height > width), fit-to-width will be calculating using half of the image width instead of the full width.
    - The intent is for when viewing standard page images that includes image files that are two physical pages joined together, i.e. full-page spreads. This _should_ keep the zoom level roughly consistent with the rest of the book.
    - This will lead to false positive if viewing landscape pages, or any digital art that doesn't try to adhere to a standard page layout. It can be toggled via a hotkey. This will automatically resize the image.
    - There's no indication that this is being done, so if two pages are joined together but don't have shared art and contain ample margins, it will be easy to accidentally skip pages.


# Removed features
For the most part, existing functionality is being kept intact. A few things were dropped either due to difficulty porting the code from Python2 to Python3, or because they aren't needed any more.
- Support for mangafox and onemanga was removed. Neither site is still active. The relevant code could be repurposed for other website(s) with a public API, but I would rather focus on being an offline reader.
- *Embedded* RAR support was removed. RAR files can still be opened as long as winrar is installed. 
- Internally, GDI is longer supported. I have not been able to get it to work with embedded files.

# Porting progress
Most of the 2 -> 3 conversion was automatic, which did leave some artifacts that need to be cleaned up. It's also likely there's some real division that needs to be corrected. Some of the Unicode hacks were removed, but others may remain. Python3 should give much better Unicode support overall.

- Updated to support Python 3.11.3. Minimum required version is Python 3.6 due to the use of fstrings.
- wx updated to 4.2.0
- wx.lib.pubsub was split off of Wx as Pypubsub; version 4.0.3 is used.
- Image display supports Freeimage and PIL (Pillow). GDI works for local files only, not files within compressed archives. Cairo can be used to speed up zooming operations.
- Removed online manga reader support. This is mostly to simplify the conversion process, as it allowed dropping httplib and beautifulsoup from the project
- Removed third party path utlity; pathlib (core Python module) is used instead.
- Only minimal testing has been done in Linux. The console logs numerous warnings about key accelerators, but for the most part the app works (tested in an Ubuntu VM)
- Tests haven't been modified, except for the automated conversion.

# Known Issues
- 16-bit precision images do not work with freeimage. PIL support is hackish.
- The wallpaper dialog broke due to other changes to the canvas and I haven't bothered to fix it.

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
- Always drag image with left mouse
- Drag image
- Full move up
- Full move down
- Full move left
- Full move right
- View images right-to-left
- Show &spread
- Attempt to show combined pages at regular zoom
