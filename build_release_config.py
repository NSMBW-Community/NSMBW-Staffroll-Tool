import os.path

PROJECT_NAME = 'NSMBW Staffroll Tool'
FULL_PROJECT_NAME = 'NSMBW Staffroll Tool'
PROJECT_VERSION = '1.0'

MAC_BUNDLE_IDENTIFIER = 'roadrunnerwmc.nsmbwstaffrolltool'

SCRIPT_FILE = 'staffroll.py'
DATA_FOLDERS = []
DATA_FILES = ['README.md', 'LICENSE']
EXTRA_IMPORT_PATHS = []

# macOS only
AUTO_APP_BUNDLE_NAME = SCRIPT_FILE.split('.')[0] + '.app'
FINAL_APP_BUNDLE_NAME = FULL_PROJECT_NAME + '.app'
