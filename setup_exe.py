#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    python setup.py py2exe
"""

from distutils.core import setup
import py2exe
from gluon.import_all import base_modules, contributed_modules
import os
import fnmatch

class reglob:
    def __init__(self, directory, pattern="*"):
        self.stack = [directory]
        self.pattern = pattern
        self.files = []
        self.index = 0
    def __getitem__(self, index):
        while 1:
            try:
                file = self.files[self.index]
                self.index = self.index + 1
            except IndexError:
                self.index = 0
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
            else:
                fullname = os.path.join(self.directory, file)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    self.stack.append(fullname)
                if not (file.startswith('.') or file.startswith('#') or file.endswith('~')) \
                        and fnmatch.fnmatch(file, self.pattern):
                    return fullname

setup(
  console=['web2py.py'],
  windows=[{'script':'web2py.py',
    'dest_base':'web2py_no_console',    #MUST NOT be just 'web2py' otherwise
                                        #it overrides the standard web2py.exe
    }],
  data_files=[
        'NEWINSTALL',
        'ABOUT',
        'LICENSE',
        'VERSION',
        ] + \
          [x for x in reglob('applications/examples')] + \
          [x for x in reglob('applications/welcome')] + \
          [x for x in reglob('applications/admin')],
  options={'py2exe': {
    'packages': contributed_modules,
    'includes': base_modules,
    }},
  )
