# -*- mode: python ; coding: utf-8 -*-

#pyinstaller quivi.spec

from glob import glob

#import quivilib.meta
#sigh.

APPNAME = 'Quivi'
USE_FREEIMAGE = False

block_cipher = None

datas=[('LICENSE.txt', '.')]
if USE_FREEIMAGE:
    datas.append(('FreeImage.dll', '.'), ('freeimage-license.txt', '.'))
translation_files = glob('localization/*.mo') + ['localization/default.pot']
for mo in translation_files:
    datas.append((mo, 'localization'))

a = Analysis(['quivi.pyw'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name=APPNAME,
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
               name=APPNAME)
