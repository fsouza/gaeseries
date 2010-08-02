#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of web2py Web Framework (Copyrighted, 2007-2010).
Developed by Massimo Di Pierro <mdipierro@cs.depaul.edu>.
License: GPL v2

Functions required to execute app components
============================================

FOR INTERNAL USE ONLY
"""

import os
import stat
import thread

cfs = {}  # for speed-up
cfs_lock = thread.allocate_lock()  # and thread safety


def getcfs(key, filename, filter=None):
    """
    Caches the *filtered* file `filename` with `key` until the file is
    modified.

    :param key: the cache key
    :param filename: the file to cache
    :param filter: is the function used for filtering. Normally `filename` is a
        .py file and `filter` is a function that bytecode compiles the file.
        In this way the bytecode compiled file is cached. (Default = None)

    This is used on Google App Engine since pyc files cannot be saved.
    """
    t = os.stat(filename)[stat.ST_MTIME]
    cfs_lock.acquire()
    item = cfs.get(key, None)
    cfs_lock.release()
    if item and item[0] == t:
        return item[1]
    if not filter:
        fp = open(filename, 'r')
        data = fp.read()
        fp.close()
    else:
        data = filter()
    cfs_lock.acquire()
    cfs[key] = (t, data)
    cfs_lock.release()
    return data
