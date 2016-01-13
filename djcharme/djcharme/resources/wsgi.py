import sys
import site
import os

# this is the path to the virtualenv python site-package dir
vepath = 'VEPATH_PAR'
# this is the path to dir parent to the django project 
djangoPath = 'DJANGO_PATH'

# this is the project's name
projectLibPath = 'PROJECT_LIB_PATH'

ALLDIRS = [vepath, projectLibPath, djangoPath]

# Remember original sys.path.
prev_sys_path = list(sys.path)

# Add each new site-packages directory.
for directory in ALLDIRS:
    site.addsitedir(directory)

# Reorder sys.path so new directories at the front.
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

