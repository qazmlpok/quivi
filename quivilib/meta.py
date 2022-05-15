# -*- coding: utf-8 -*-
import logging
import sys

APPNAME = 'Quivi'
VERSION = '2.0.0'
DESCRIPTION = 'Manga/comic reader and image viewer'
URL = 'http://quivi.sourceforge.net'
UPDATE_URL = 'http://quivi.sourceforge.net/update.php'
REPORT_URL = 'http://conradoplg.wufoo.com/forms/quivi/'
HELP_URL = 'http://quivi.sourceforge.net/documentation'
AUTHOR = 'Conrado Porto Lopes Gouvea'
AUTHOR_EMAIL = 'conradoplg@gmail.com'
COPYRIGHT = f"Copyright (c) 2009, {AUTHOR} <{AUTHOR_EMAIL}>\nAll rights reserved."

CACHE_ENABLED = True
CACHE_SIZE = 3
PREFETCH_COUNT = 1
DEBUG = False
LOG_LEVEL = logging.ERROR
DOUBLE_BUFFERING = True

if sys.platform == 'win32':
    USE_FREEIMAGE = True
    USE_PIL = True
    USE_GDI_PLUS = True
    USE_CAIRO = False
    PATH_SEP = ';'
else:
    USE_FREEIMAGE = True
    USE_PIL = False
    USE_GDI_PLUS = False
    USE_CAIRO = False
    PATH_SEP = ':'

MANIFEST = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <assemblyIdentity
        version="0.64.1.0"
        processorArchitecture="x86"
        name="Controls"
        type="win32"
    />
    <description>Quivi</description>
    <dependency>
        <dependentAssembly>
            <assemblyIdentity
                type="win32"
                name="Microsoft.Windows.Common-Controls"
                version="6.0.0.0"
                processorArchitecture="X86"
                publicKeyToken="6595b64144ccf1df"
                language="*"
            />
        </dependentAssembly>
    </dependency>
    <dependency>
        <dependentAssembly>
            <assemblyIdentity 
                type='win32' 
                name='Microsoft.VC90.CRT' 
                version='9.0.21022.8' 
                processorArchitecture='*' 
                publicKeyToken='1fc8b3b9a1e18e3b' />
        </dependentAssembly>
    </dependency>
    <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
        <security>
            <requestedPrivileges>
                <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
            </requestedPrivileges>
        </security>
    </trustInfo>
</assembly> 
"""
