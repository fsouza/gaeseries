#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file is part of web2py Web Framework (Copyrighted, 2007-2010).
Developed by Massimo Di Pierro <mdipierro@cs.depaul.edu> and
Limodou <limodou@gmail.com>.
License: GPL v2

This makes uses of the pywin32 package
(http://sourceforge.net/projects/pywin32/).
You do not need to install this package to use web2py.


"""

import time
import os
import sys
import traceback
import win32serviceutil
import win32service
import win32event
import servicemanager
import _winreg
from fileutils import up

__all__ = ['web2py_windows_service_handler']


class Service(win32serviceutil.ServiceFramework):

    _svc_name_ = '_unNamed'
    _svc_display_name_ = '_Service Template'

    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.start()
            win32event.WaitForSingleObject(self.stop_event,
                    win32event.INFINITE)
        except:
            self.log(traceback.format_exc(sys.exc_info))
            self.SvcStop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        try:
            self.stop()
        except:
            self.log(traceback.format_exc(sys.exc_info))
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    # to be overridden

    def start(self):
        pass

    # to be overridden

    def stop(self):
        pass


class Web2pyService(Service):

    _svc_name_ = 'web2py'
    _svc_display_name_ = 'web2py Service'
    _exe_args_ = 'options'
    server = None

    def chdir(self):
        try:
            h = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                r'SYSTEM\CurrentControlSet\Services\%s'
                                 % self._svc_name_)
            cls = _winreg.QueryValue(h, 'PythonClass')
            dir = os.path.dirname(cls)
            os.chdir(dir)
            return True
        except:
            self.log("Can't change to web2py working path, server is stopped")
            return False

    def start(self):
        self.log('web2py server starting')
        if not self.chdir():
            return
        if len(sys.argv) == 2:
            opt_mod = sys.argv[1]
        else:
            opt_mod = self._exe_args_
        options = __import__(opt_mod, [], [], '')
        import main
        self.server = main.HttpServer(
            ip=options.ip,
            port=options.port,
            password=options.password,
            pid_filename=options.pid_filename,
            log_filename=options.log_filename,
            profiler_filename=options.profiler_filename,
            ssl_certificate=options.ssl_certificate,
            ssl_private_key=options.ssl_private_key,
            numthreads=options.numthreads,
            server_name=options.server_name,
            request_queue_size=options.request_queue_size,
            timeout=options.timeout,
            shutdown_timeout=options.shutdown_timeout,
            path=options.folder
            )
        try:
            self.server.start()
        except:

            # self.server.stop()

            self.server = None
            raise

    def stop(self):
        self.log('web2py server stopping')
        if not self.chdir():
            return
        if self.server:
            self.server.stop()
        time.sleep(1)


def web2py_windows_service_handler(argv=None, opt_file='options'):
    path = os.path.dirname(__file__)
    classstring = os.path.normpath(os.path.join(up(path),
                                   'gluon.winservice.Web2pyService'))
    if opt_file:
        Web2pyService._exe_args_ = opt_file
        win32serviceutil.HandleCommandLine(Web2pyService,
                serviceClassString=classstring, argv=['', 'install'])
    win32serviceutil.HandleCommandLine(Web2pyService,
            serviceClassString=classstring, argv=argv)


if __name__ == '__main__':
    web2py_windows_service_handler()
