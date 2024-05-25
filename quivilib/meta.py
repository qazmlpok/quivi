# -*- coding: utf-8 -*-
import logging
import sys

APPNAME = 'Quivi'
VERSION = '2.0.5'
DESCRIPTION = 'Manga/comic reader and image viewer'
URL = 'https://github.com/qazmlpok/quivi'
UPDATE_URL = 'https://raw.githubusercontent.com/qazmlpok/quivi/master/VERSION.txt'
#UPDATE_URL = 'https://raw.githubusercontent.com/qazmlpok/quivi/fake-update/VERSION.txt'
REPORT_URL = 'https://github.com/qazmlpok/quivi/issues'
HELP_URL = 'http://quivi.sourceforge.net/documentation'
AUTHOR = 'qazmlpok'
AUTHOR_EMAIL = 'qazmlpok@gmail.com'
ORIG_AUTHOR = 'Conrado Porto Lopes Gouvea'
ORIG_AUTHOR_EMAIL = 'conradoplg@gmail.com'
COPYRIGHT = f"Copyright (c) 2009, {ORIG_AUTHOR} <{ORIG_AUTHOR_EMAIL}>\nCopyright (c) 2022, {AUTHOR} <{AUTHOR_EMAIL}>\nAll rights reserved."

CACHE_ENABLED = True
CACHE_SIZE = 7
PREFETCH_COUNT = 2
if __debug__:
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
else:
    DEBUG = False
    LOG_LEVEL = logging.ERROR
DOUBLE_BUFFERING = True

#GDI is used to speed up image processing on Windows. Roughly 10% faster from my tests.
#However, it only supports basic image types and does not support files within zip archives.
if sys.platform == 'win32':
    USE_FREEIMAGE = False
    USE_PIL = True
    USE_GDI_PLUS = False
    USE_CAIRO = True
    PATH_SEP = ';'
else:
    USE_FREEIMAGE = True
    USE_PIL = True
    USE_GDI_PLUS = False
    USE_CAIRO = True
    PATH_SEP = ':'

#This isn't being used. But I don't know what should go into a manifest, so I'm leaving it alone.
MANIFEST = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="quivi" processorArchitecture="amd64" version="1.0.0.0"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" language="*" processorArchitecture="*" version="6.0.0.0" publicKeyToken="6595b64144ccf1df"/>
    </dependentAssembly>
  </dependency>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </windowsSettings>
  </application>
</assembly>
"""
