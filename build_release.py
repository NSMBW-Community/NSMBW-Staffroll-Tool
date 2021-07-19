#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os, os.path
import shutil
import sys

import PyInstaller.__main__


########################################################################
############################### Constants ##############################
########################################################################

import build_release_config as config


########################################################################
################################# Intro ################################
########################################################################

DIR = 'distrib'
WORKPATH = 'build_temp'
SPECFILE = config.SCRIPT_FILE[:-3] + '.spec'

def print_emphasis(s):
    print('>>')
    print('>> ' + '=' * (len(s) - 3))
    print(s)
    print('>> ' + '=' * (len(s) - 3))
    print('>>')

print('[[ Building ' + config.PROJECT_NAME + ' ]]')
print('>> Please note: extra command-line arguments passed to this script will be passed through to PyInstaller.')
print('>> Destination directory: ' + DIR)

if os.path.isdir(DIR): shutil.rmtree(DIR)
if os.path.isdir(WORKPATH): shutil.rmtree(WORKPATH)
if os.path.isdir(SPECFILE): os.remove(SPECFILE)

def run_pyinstaller(args):
    print('>>')
    printMessage = ['>> Running PyInstaller with the following arguments:']
    for a in args:
        if ' ' in a:
            printMessage.append('"' + a + '"')
        else:
            printMessage.append(a)
    print(' '.join(printMessage))
    print('>>')

    PyInstaller.__main__.run(args)


########################################################################
######################### Environment detection ########################
########################################################################
print('>>')
print('>> Detecting environment...')
print('>>')

# Python optimization level
if sys.flags.optimize == 2:
    print('>>   [X] Python optimization level is -OO')
else:
    print('>>   [ ] Python optimization level is -OO')


########################################################################
######################### Excludes and Includes ########################
########################################################################
print('>>')
print('>> Populating excludes and includes...')
print('>>')

# Excludes
excludes = ['calendar', 'datetime', 'difflib', 'doctest', 'inspect',
    'locale', 'multiprocessing', 'optpath', 'os2emxpath', 'pdb',
    'socket', 'ssl', 'unittest',
    'FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter',
    'select', 'threading', 'hashlib']

if sys.platform == 'nt':
    excludes.append('posixpath')

# Includes
includes = ['pkgutil']

# Binary excludes
excludes_binaries = []
if sys.platform == 'win32':
    excludes_binaries = [
        'opengl32sw.dll',
        'd3dcompiler_',  # currently (2020-09-25) "d3dcompiler_47.dll",
                         # but that'll probably change eventually, so we
                         # just exclude anything that starts with this
                         # substring
    ]

elif sys.platform == 'darwin':
    # Sadly, we can't exclude anything on macOS -- it just crashes. :(
    pass

elif sys.platform == 'linux':
    excludes_binaries = [
        'libgtk-3.so',
    ]


print('>> Will use the following excludes list: ' + ', '.join(excludes))
print('>> Will use the following includes list: ' + ', '.join(includes))
print('>> Will use the following binaries excludes list: ' + ', '.join(excludes_binaries))


########################################################################
################### Running PyInstaller (first time) ###################
########################################################################

# Our only goal here is to create a specfile we can edit. Unfortunately,
# there's no good way to do that without doing a full PyInstaller
# build...

args = [
    '--onefile',
    '--distpath=' + DIR,
    '--workpath=' + WORKPATH,
]

if sys.platform == 'darwin':
    args.append('--osx-bundle-identifier=' + config.MAC_BUNDLE_IDENTIFIER)

for e in excludes:
    args.append('--exclude-module=' + e)
for i in includes:
    args.append('--hidden-import=' + i)
args.extend(sys.argv[1:])
args.append(config.SCRIPT_FILE)

run_pyinstaller(args)

shutil.rmtree(DIR)
shutil.rmtree(WORKPATH)


########################################################################
########################## Adjusting specfile ##########################
########################################################################
print('>> Adjusting specfile...')

# New plist file data (if on Mac)
info_plist = {
    'CFBundleName': config.PROJECT_NAME,
    'CFBundleDisplayName': config.FULL_PROJECT_NAME,
    'CFBundleShortVersionString': config.PROJECT_VERSION,
    'CFBundleGetInfoString': config.FULL_PROJECT_NAME + ' ' + config.PROJECT_VERSION,
    'CFBundleExecutable': config.SCRIPT_FILE.split('.')[0],
}

# Open original specfile
with open(SPECFILE, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

# Iterate over its lines, and potentially add new ones
new_lines = []
for line in lines:
    if 'PYZ(' in line and excludes_binaries:
        new_lines.append('EXCLUDES = ' + repr(excludes_binaries))
        new_lines.append('new_binaries = []')
        new_lines.append('for x, y, z in a.binaries:')
        new_lines.append('    for e in EXCLUDES:')
        new_lines.append('        if x.startswith(e):')
        new_lines.append('            print("specfile: excluding " + x)')
        new_lines.append('            break')
        new_lines.append('    else:')
        new_lines.append('        new_binaries.append((x, y, z))')
        new_lines.append('a.binaries = new_binaries')

    new_lines.append(line)

    if sys.platform == 'darwin' and 'BUNDLE(' in line:
        new_lines.append('info_plist=' + json.dumps(info_plist) + ',')

# Save new specfile
with open(SPECFILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))



########################################################################
################### Running PyInstaller (second time) ##################
########################################################################

# Most of the arguments are now contained in the specfile. Thus, we can
# run with minimal arguments this time.

args = [
    '--distpath=' + DIR,
    '--workpath=' + WORKPATH,
    SPECFILE,
]

run_pyinstaller(args)

shutil.rmtree(WORKPATH)
os.remove(SPECFILE)


########################################################################
######################## Copying required files ########################
########################################################################
print('>> Copying required files...')

if sys.platform == 'darwin':
    dest_folder = os.path.join(DIR, config.AUTO_APP_BUNDLE_NAME, 'Contents', 'Resources')
else:
    dest_folder = DIR

if not os.path.isdir(dest_folder):
    os.makedirs(dest_folder)

for f in config.DATA_FOLDERS:
    if os.path.isdir(os.path.join(dest_folder, f)):
        shutil.rmtree(os.path.join(dest_folder, f))
    shutil.copytree(f, os.path.join(dest_folder, f))

for f in config.DATA_FILES:
    shutil.copy(f, dest_folder)


########################################################################
################################ Cleanup ###############################
########################################################################
print('>> Cleaning up...')

# On macOS, there's a second "reggie" executable for some reason,
# separate from the app bundle. I don't know why it's there, but we
# delete it.

if sys.platform == 'darwin':
    leftover_executable = os.path.join(DIR, config.SCRIPT_FILE.split('.')[0])
    if os.path.isfile(leftover_executable):
        os.unlink(leftover_executable)

# Also on macOS, we have to rename the .app folder to the display name
# because CFBundleDisplayName is dumb and doesn't actually affect
# the app name shown in Finder
if sys.platform == 'darwin':
    os.rename(os.path.join(DIR, config.AUTO_APP_BUNDLE_NAME), os.path.join(DIR, config.FINAL_APP_BUNDLE_NAME))


########################################################################
################################## End #################################
########################################################################
print('>> %s has been built to the %s folder!' % (config.PROJECT_NAME, DIR))
