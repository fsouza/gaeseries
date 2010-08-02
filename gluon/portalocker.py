#!/usr/bin/env python
# -*- coding: utf-8 -*-
# portalocker.py - Cross-platform (posix/nt) API for flock-style file locking.
#                  Requires python 1.5.2 or better.

"""
Cross-platform (posix/nt) API for flock-style file locking.

Synopsis:

   import portalocker
   file = open(\"somefile\", \"r+\")
   portalocker.lock(file, portalocker.LOCK_EX)
   file.seek(12)
   file.write(\"foo\")
   file.close()

If you know what you're doing, you may choose to

   portalocker.unlock(file)

before closing the file, but why?

Methods:

   lock( file, flags )
   unlock( file )

Constants:

   LOCK_EX
   LOCK_SH
   LOCK_NB

I learned the win32 technique for locking files from sample code
provided by John Nielsen <nielsenjf@my-deja.com> in the documentation
that accompanies the win32 modules.

Author: Jonathan Feinberg <jdf@pobox.com>
Version: $Id: portalocker.py,v 1.3 2001/05/29 18:47:55 Administrator Exp $
"""

import os
import logging

os_locking = None
try:
    import fcntl
    os_locking = 'posix'
except:
    pass
try:
    import win32con
    import win32file
    import pywintypes
    os_locking = 'windows'
except:
    pass

if os_locking == 'windows':
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # the default
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY

    # is there any reason not to reuse the following structure?

    __overlapped = pywintypes.OVERLAPPED()

    def lock(file, flags):
        hfile = win32file._get_osfhandle(file.fileno())
        win32file.LockFileEx(hfile, flags, 0, 0x7fff0000, __overlapped)

    def unlock(file):
        hfile = win32file._get_osfhandle(file.fileno())
        win32file.UnlockFileEx(hfile, 0, 0x7fff0000, __overlapped)


elif os_locking == 'posix':
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB

    def lock(file, flags):
        fcntl.flock(file.fileno(), flags)

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


else:
    logging.warning('no file locking')
    LOCK_EX = None
    LOCK_SH = None
    LOCK_NB = None

    def lock(file, flags):
        pass

    def unlock(file):
        pass


if __name__ == '__main__':
    from time import time, strftime, localtime
    import sys

    log = open('log.txt', 'a+')
    lock(log, LOCK_EX)

    timestamp = strftime('%m/%d/%Y %H:%M:%S\n', localtime(time()))
    log.write(timestamp)

    print 'Wrote lines. Hit enter to release lock.'
    dummy = sys.stdin.readline()

    log.close()
