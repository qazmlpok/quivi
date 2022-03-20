"""Distutils setup script."""

from quivilib import meta

import sys
import os
import re
from glob import glob
from shutil import copy

if sys.platform == 'win32':
    # ModuleFinder can't handle runtime changes to __path__, but win32com uses them
    try:
        # if this doesn't work, try import modulefinder
        import py2exe.mf as modulefinder
        import win32com
        for p in win32com.__path__[1:]:
            modulefinder.AddPackagePath("win32com", p)
        for extra in ["win32com.shell"]: #,"win32com.mapi"
            __import__(extra)
            m = sys.modules[extra]
            for p in m.__path__[1:]:
                modulefinder.AddPackagePath(extra, p)
    except ImportError:
        # no build path setup, no worries.
        pass


from distutils.core import setup

#If we want to build a py2exe dist, patch distutils with py2exe
try:
    if 'py2exe' in sys.argv:
        import py2exe
except ImportError:
    pass

#If we want to build a egg dist, patch distutils with setuptools
try:
    if 'bdist_egg' in sys.argv:
        from setuptools import setup
except ImportError:
    pass


#Auto find subpackages
def do_walk():
    packages = []
    files = os.walk('quivilib')
    for (dirpath, dirnames, filenames) in files:
        if '__init__.py' in filenames:
            packages.append(
                re.sub('.*quivilib', 'quivilib', dirpath)
                .replace(os.path.sep, '.')
            )
    return packages

packages = do_walk()
if meta.USE_FREEIMAGE:
    packages.append('pyfreeimage')

if sys.platform == 'win32':
    #main_files = ['LICENSE.txt', 'VCOMP140.DLL', 'VCRUNTIME140.dll']
    main_files = ['LICENSE.txt']
    if meta.USE_FREEIMAGE:
        main_files.append('FreeImage.dll', 'freeimage-license.txt')
    translation_files = glob('localization/*.mo') + ['localization/default.pot']
    data_files = [('', main_files),
                  ('localization', translation_files)]
    scripts = ['quivi.pyw']
else:
    data_files = [
                  ('share/applications', ['resources/quivi.desktop']),
                  ('share/pixmaps', ['resources/icons/48x48/quivi.png']),
                  ('share/icons/hicolor/scalable/apps', ['resources/icons/scalable/quivi.svg']),
                  ('share/icons/hicolor/16x16/apps', ['resources/icons/16x16/quivi.png']),
                  ('share/icons/hicolor/32x32/apps', ['resources/icons/32x32/quivi.png']),
                  ('share/icons/hicolor/48x48/apps', ['resources/icons/48x48/quivi.png']),
                 ]
    MO_DIR = 'localization'
    for mo in glob(os.path.join(MO_DIR, '*.mo')):
        lang = os.path.basename(mo[:-3])
        nmo = os.path.join(MO_DIR, lang, 'quivi.mo')
        directory = os.path.dirname(nmo)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copy(mo, nmo)
        dest = os.path.dirname(os.path.join('share', 'locale', lang, 'LC_MESSAGES', 'quivi.mo'))
        data_files.append((dest, [nmo]))
    copy('quivi.pyw', 'quivi')
    scripts = ['quivi']

include_packages = ['pubsub', 'pubsub.core']
exclude_packages = ["Tkconstants", "Tkinter", "tcl", 'pydoc', '_ssl', 'numpy', 'tkinter']
if not meta.USE_PIL:
    exclude_packages.append('Image')
if not meta.USE_CAIRO:
    exclude_packages.append('cairo')
    exclude_packages.append('wx.lib.wxcairo')


setup(name=meta.APPNAME,
      version=meta.VERSION,
      description=meta.APPNAME,
      author=meta.AUTHOR,
      author_email=meta.AUTHOR_EMAIL,
      packages = packages,
      license = "MIT",
      url = meta.URL,
      options = {'py2exe': {'dist_dir': 'bin',
                            'excludes': exclude_packages,
                            'includes': include_packages,
                            "include_msvcr": True,
                            }
                },
      windows= [{'script': 'quivi.pyw',
                 'icon_resources': [(1, 'resources/quivi.ico'),
                                    (2, 'resources/quivi.ico')],
                 'other_resources': [(24,1,meta.MANIFEST)]
                 }],
      scripts = scripts,
      data_files = data_files
      )
