ISCC = '"C:/Program Files (x86)/Inno Setup 6/ISCC.exe"'
ISS = 'Quivi.iss'
ISSTMPL = 'Quivi.iss.tmpl'
PYINST = 'pyinstaller.EXE'
SPECFILE = 'quivi.spec'

ZIP = '"C:/Program Files/7-Zip/7z.exe"'

import os
import shutil

to_remove = ['build', 'dist', 'Output']
for dirname in to_remove:
    if os.path.exists(dirname):
        print("Clearing directory", dirname)
        shutil.rmtree(dirname)

#Delete the temp ISS file.
if os.path.isfile(ISS):
    os.remove(ISS)

from quivilib import meta

#Needed to turn off debug mode
os.environ["PYTHONOPTIMIZE"] = "1"

print(meta.APPNAME, '-', meta.VERSION)

#Don't include extension
INSTALLER_FILENAME = f'{meta.APPNAME}-{meta.VERSION}'
INSTALLER_OUTDIR = 'Output'
INSTALLER_OUTPATH = os.path.join(INSTALLER_OUTDIR, INSTALLER_FILENAME)

#Run PyInstaller to create the build folder.
ret = os.system(f'{PYINST} {SPECFILE} --noconfirm')
DISTFOLDER = os.path.join('dist', meta.APPNAME)

if (not os.path.exists(DISTFOLDER)):
    print("dist folder doesn't exist", DISTFOLDER)
    exit()

#Create a zip of the build folder.
cwd = os.getcwd()

zipFilename = os.path.join(cwd, INSTALLER_OUTDIR, f'{INSTALLER_FILENAME}-standalone.zip')

os.chdir(DISTFOLDER)
print("SYS", f'{ZIP} a {zipFilename} *')
ret = os.system(f'{ZIP} a {zipFilename} *')
if (ret != 0):
    print("Call to ZIP failed.")
    exit()
if (not os.path.exists(zipFilename)):
    print("Call to ZIP failed.")
    exit()
os.chdir(cwd)


#Do simple string substitution on the .iss.tmpl file to create the iss file.
with open(ISSTMPL, 'r') as infile:
    data = infile.read()
    data = data.replace('||APPNAME||', meta.APPNAME) \
                .replace('||VERSION||', meta.VERSION) \
                .replace('||URL||', meta.URL)
    with open(ISS, 'w') as outfile:
        outfile.write(data)

#Run InnoSetup
ret = os.system(f'{ISCC} {ISS} /O{INSTALLER_OUTDIR} /F{INSTALLER_FILENAME}')



if (ret != 0):
    print("Setup compilation failed.")
    exit()
if (not os.path.exists(f'{INSTALLER_OUTPATH}.exe')):
    print("Can't find the installer.", INSTALLER_OUTPATH)
    exit()

