# Quivi
Quivi is an image viewer (specialized for comic/manga reading) which supports many file formats and compressed (zip, rar) files. It is aimed for fast & easy file browsing with keyboard or mouse. 
 
The home page for the original distribution of Quivi is http://quivi.sourceforge.net/

 

# quivi-64
This fork was made with the primary purpose of adding 64-bit compatibility. The original Python code has been ported to Python 3.

No new features have been added, but the upgrade to Python 3 offers better support for Unicode filenames, and the 64bit environment supports larger images.

Upgrading the image libraries offers support for some newer formats, including Webp.

# Porting progress
- Updated to support Python 3.10.6
- wx updated to 4.2.0
- wx.lib.pubsub was split off of Wx as Pypubsub; version 4.0.3 is used.
- Image display supports GTK, Freeimage, and PIL (Pillow) works. Cairo is not supported.
- Removed online manga reader support. This is mostly to simplify the conversion process, as it allowed dropping httplib and beautifulsoup from the project
- Removed third party path utlity; pathlib (core Python module) is used instead.
- Only minimal testing has been done in Linux. The console logs numerous warnings about key accelerators, but for the most part the app works (tested in Ubuntu)
- Tests haven't been modified, except for the automated conversion

Most of the 2 -> 3 conversion was automatic, which did leave some artifacts that need to be cleaned up. It's also likely there's some real division that needs to be corrected. Some of the Unicode hacks were removed, but others may remain. Python3 should give much better Unicode support overall.
