# quivi-64
Fork of [Quivi](http://quivi.sourceforge.net/index.en.html), with the primary purpose of adding 64-bit compatibility. The original Python code (is in the process of) being ported to Python 3

# Porting progress
- Updated to support Python 3.8.1
- wx updated to 4.1.1
- Freeimage is currently disabled. Image display via PIL (Pillow) works.
- Removed online manga reader support. This is mostly to simplify the conversion process, as it allowed dropping httplib and beautifulsoup from the project
- Removed third party path utlity, use pathlib (core Python module) instead.
- No testing has been done in Linux
- Tests haven't been run or modified (except for the automated conversion)

Most of the 2 -> 3 conversion was automatic, which did leave some artifacts that need to be cleaned up. It's also likely there's some real division that needs to be corrected. Some of the Unicode hacks were removed, but others may remain. Python3 should give much better Unicode support overall.

wx.lib.pubsub is deprecated and needs to be replaced with pypubsub.

The arg1 messaging protocol is deprecated and needs to be replaced.

The main window no longer supports drag & drop due to a conflict in wx; this needs a workaround (new component?) or a fix.

