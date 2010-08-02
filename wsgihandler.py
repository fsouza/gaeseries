#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a WSGI handler for Apache
Requires apache+mod_wsgi.

In httpd.conf put something like:

    LoadModule wsgi_module modules/mod_wsgi.so
    WSGIScriptAlias / /path/to/wsgihandler.py

"""

# change these parameters as required
LOGGING = False
SOFTCRON = False

import sys
import os
sys.path.insert(0, '')
path = os.path.dirname(os.path.abspath(__file__))
if not path in sys.path:
    sys.path.append(path)
    sys.path.append(os.path.join(path,'site-packages'))
os.chdir(path)
import gluon.main

if LOGGING:
    application = gluon.main.appfactory(wsgiapp=gluon.main.wsgibase,
                                        logfilename='httpserver.log',
                                        profilerfilename=None)
else:
    application = gluon.main.wsgibase

if SOFTCRON:
    from settings import settings
    settings.web2py_crontype = 'soft'
