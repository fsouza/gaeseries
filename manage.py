#!/usr/bin/env python

# Add "common-apps" folder to sys.path if it exists
import os, sys
common_dir = os.path.join(os.path.dirname(__file__), 'common-apps')
if os.path.exists(common_dir):
    sys.path.append(common_dir)

# Initialize App Engine SDK if djangoappengine backend is installed
try:
    from djangoappengine.boot import setup_env
except ImportError:
    pass
else:
    setup_env()

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
