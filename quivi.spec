# -*- mode: python ; coding: utf-8 -*-

#pyinstaller quivi.spec

from glob import glob

#Importing the module here requires using the full path. I don't know why.
#Taken from https://stackoverflow.com/questions/66345912
import os
import importlib.util
cwd = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "package", cwd + "/quivilib/meta.py"
)
meta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meta)




block_cipher = None

datas=[('LICENSE.txt', '.')]
excludes = []
if meta.USE_FREEIMAGE:
    datas.append(('freeimage-license.txt', '.'))
if meta.USE_CAIRO:
    datas.append(('cairo.dll', '.'))
translation_files = glob('localization/*.mo') + ['localization/default.pot']
for mo in translation_files:
    datas.append((mo, 'localization'))

#Don't include packages that are disabled by configuration
if not meta.USE_CAIRO:
    excludes.append('cairo')
if not meta.USE_PIL:
    excludes.append('PIL')

a = Analysis(['quivi.pyw'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if not meta.USE_FREEIMAGE:
    a.binaries = a.binaries - TOC([
        ('freeimage.dll', None, None),
    ])

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name=meta.APPNAME,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          #Manifest seems unnecessary
          entitlements_file=None , version='file_version_info.txt', icon='resources\\quivi.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name=meta.APPNAME)
