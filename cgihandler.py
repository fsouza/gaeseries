#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import wsgiref.handlers

sys.path.insert(0, '')
path = os.path.dirname(os.path.abspath(__file__))
if not path in sys.path:
    sys.path.append(path)
    sys.path.append(os.path.join(path,'site-packages'))
os.chdir(path)

import gluon.main

wsgiref.handlers.CGIHandler().run(gluon.main.wsgibase)
