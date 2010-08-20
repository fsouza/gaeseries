# -*- coding: utf-8 -*-
"""
    tipfy.ext.debugger.app
    ~~~~~~~~~~~~~~~~~~~~~~

    Debugger extension, to be used in development only.

    Applies monkeypatch for Werkzeug's interactive debugger to work with
    the development server. See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import os
import sys

from jinja2 import Environment, FileSystemLoader

# Set the template environment.
env = Environment(loader=FileSystemLoader(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'templates'))))


# werkzeug.debug.utils
def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


def get_debugged_app(app):
    from werkzeug import DebuggedApplication
    return DebuggedApplication(app, evalex=True)


# Monkeypatches
# -------------
# werkzeug.debug.console.HTMLStringO
def seek(self, n, mode=0):
    pass


def readline(self):
    if len(self._buffer) == 0:
        return ''
    ret = self._buffer[0]
    del self._buffer[0]
    return ret


# Patch utils first, to avoid loading Werkzeug's template.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]


# Apply all other patches.
from werkzeug.debug.console import HTMLStringO
HTMLStringO.seek = seek
HTMLStringO.readline = readline
