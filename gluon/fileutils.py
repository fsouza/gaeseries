#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of web2py Web Framework (Copyrighted, 2007-2010).
Developed by Massimo Di Pierro <mdipierro@cs.depaul.edu>.
License: GPL v2
"""

import storage
import os
import re
import tarfile
import glob
from http import HTTP
from gzip import open as gzopen


__all__ = [
    'up',
    'listdir',
    'cleanpath',
    'tar',
    'untar',
    'tar_compiled',
    'get_session',
    'check_credentials',
    'w2p_pack',
    'w2p_unpack',
    'w2p_pack_plugin',
    'w2p_unpack_plugin',
    'fix_newlines',
    ]


def listdir(
    path,
    expression='^.+$',
    drop=True,
    add_dirs=False,
    ):
    """
    like os.listdir() but you can specify a regex patter to filter filed.
    if add_dirs==True the returned items will have the full path.
    """

    if path[-1:] != '/':
        path = path + '/'
    if drop:
        n = len(path)
    else:
        n = 0
    regex = re.compile(expression)
    items = []
    for (root, dirs, files) in os.walk(path, topdown=True):
        for dir in dirs[:]:
            if dir.startswith('.'):
                dirs.remove(dir)
        if add_dirs:
            items.append(root[n:])
        for file in files:
            if regex.match(file) and not file.startswith('.'):
                items.append(os.path.join(root, file)[n:])
    return sorted(items)


def cleanpath(path):
    """
    turns any expression/path into a valid filename. replaces / with _ and
    removes special characters.
    """

    items = path.split('.')
    if len(items) > 1:
        path = re.sub('[^\w\.]+', '_', '_'.join(items[:-1]) + '.'
                       + ''.join(items[-1:]))
    else:
        path = re.sub('[^\w\.]+', '_', ''.join(items[-1:]))
    return path


def _extractall(filename, path='.', members=None):
    if not hasattr(tarfile.TarFile, 'extractall'):
        from tarfile import ExtractError

        class TarFile(tarfile.TarFile):

            def extractall(self, path='.', members=None):
                """Extract all members from the archive to the current working
             directory and set owner, modification time and permissions on
             directories afterwards. `path' specifies a different directory
             to extract to. `members' is optional and must be a subset of the
             list returned by getmembers().
                """

                directories = []
                if members is None:
                    members = self
                for tarinfo in members:
                    if tarinfo.isdir():

                        # Extract directory with a safe mode, so that
                        # all files below can be extracted as well.

                        try:
                            os.makedirs(os.path.join(path,
                                    tarinfo.name), 0777)
                        except EnvironmentError:
                            pass
                        directories.append(tarinfo)
                    else:
                        self.extract(tarinfo, path)

                # Reverse sort directories.

                directories.sort(lambda a, b: cmp(a.name, b.name))
                directories.reverse()

                # Set correct owner, mtime and filemode on directories.

                for tarinfo in directories:
                    path = os.path.join(path, tarinfo.name)
                    try:
                        self.chown(tarinfo, path)
                        self.utime(tarinfo, path)
                        self.chmod(tarinfo, path)
                    except ExtractError, e:
                        if self.errorlevel > 1:
                            raise
                        else:
                            self._dbg(1, 'tarfile: %s' % e)


        _cls = TarFile
    else:
        _cls = tarfile.TarFile

    tar = _cls(filename, 'r')
    ret = tar.extractall(path, members)
    tar.close()
    return ret

def tar(file, dir, expression='^.+$'):
    """
    tars dir into file, only tars file that match expression
    """

    tar = tarfile.TarFile(file, 'w')
    for file in listdir(dir, expression, add_dirs=True):
        tar.add(os.path.join(dir, file), file, False)
    tar.close()

def untar(file, dir):
    """
    untar file into dir
    """

    _extractall(file, dir)


def w2p_pack(filename, path, compiled=False):
    tarname = filename + '.tar'
    if compiled:
        tar_compiled(tarname, path, '^[\w\.\-]+$')
    else:
        tar(tarname, path, '^[\w\.\-]+$')
    w2pfp = gzopen(filename, 'wb')
    tarfp = open(tarname, 'rb')
    w2pfp.write(tarfp.read())
    w2pfp.close()
    tarfp.close()
    os.unlink(tarname)


def w2p_unpack(filename, path, delete_tar=True):
    if filename[-4:] == '.w2p' or filename[-3:] == '.gz':
        if filename[-4:] == '.w2p':
            tarname = filename[:-4] + '.tar'
        else:
            tarname = filename[:-3] + '.tar'
        fgzipped = gzopen(filename, 'rb')
        tarfile = open(tarname, 'wb')
        tarfile.write(fgzipped.read())
        tarfile.close()
        fgzipped.close()
    else:
        tarname = filename
    untar(tarname, path)
    if delete_tar:
        os.unlink(tarname)


def w2p_pack_plugin(filename, path, plugin_name):
    """Pack the given plugin into a w2p file.
    Will match files at:
        <path>/*/plugin_[name].*
        <path>/*/plugin_[name]/*
    """
    if not filename.endswith('web2py.plugin.%s.w2p' % plugin_name):
        raise Exception, "Not a web2py plugin name"
    plugin_tarball = tarfile.open(filename, 'w:gz')
    app_dir = path
    while app_dir[-1]=='/':
        app_dir = app_dir[:-1]
    files1=glob.glob(os.path.join(app_dir,'*/plugin_%s.*' % plugin_name))
    files2=glob.glob(os.path.join(app_dir,'*/plugin_%s/*' % plugin_name))
    for file in files1+files2:
        plugin_tarball.add(file, arcname=file[len(app_dir)+1:])
    plugin_tarball.close()


def w2p_unpack_plugin(filename, path, delete_tar=True):
    if not os.path.basename(filename).startswith('web2py.plugin.'):
        raise Exception, "Not a web2py plugin"
    w2p_unpack(filename,path,delete_tar)


def tar_compiled(file, dir, expression='^.+$'):
    """
    used to tar a compiled application.
    the content of models, views, controllers is not stored in the tar file.
    """

    tar = tarfile.TarFile(file, 'w')
    for file in listdir(dir, expression, add_dirs=True):
        filename = os.path.join(dir, file)
        if os.path.islink(filename):
            continue
        if os.path.isfile(filename) and file[-4:] != '.pyc':
            if file[:6] == 'models':
                continue
            if file[:5] == 'views':
                continue
            if file[:11] == 'controllers':
                continue
            if file[:7] == 'modules':
                continue
        tar.add(filename, file, False)
    tar.close()

def up(path):
    return os.path.dirname(os.path.normpath(path))


def get_session(request, other_application='admin'):
    """ checks that user is authorized to access other_application"""

    if request.application == other_application:
        raise KeyError
    try:
        session_id = request.cookies['session_id_'
                 + other_application].value
        osession = \
            storage.load_storage(os.path.join(up(request.folder),
                                 other_application, 'sessions',
                                 session_id))
    except:
        osession = storage.Storage()
    return osession


def check_credentials(request, other_application='admin'):
    """ checks that user is authorized to access other_application"""

    if request.env.web2py_runtime_gae:
        from google.appengine.api import users
        if users.is_current_user_admin():
            return True
        else:
            login_html = '<a href="%s">Sign in with your google account</a>.' \
                % users.create_login_url(request.env.path_info)
            raise HTTP(200, '<html><body>%s</body></html>' % login_html)
    else:
        return get_session(request, other_application).authorized


def fix_newlines(path):
    regex = re.compile(r'''(\r
|\r|
)''')
    for filename in listdir(path, '.*\.(py|html)$', drop=False):
        fp = open(filename, 'rb')
        rdata = fp.read()
        fp.close()
        wdata = regex.sub('\n', rdata)
        if wdata != rdata:
            fp = open(filename, 'wb')
            fp.write(wdata)
            fp.close()

def copystream(
    src,
    dest,
    size,
    chunk_size=10 ** 5,
    ):
    """
    this is here because I think there is a bug in shutil.copyfileobj
    """
    while size > 0:
        if size < chunk_size:
            data = src.read(size)
        else:
            data = src.read(chunk_size)
        length = len(data)
        if length > size:
            (data, length) = (data[:size], size)
        size -= length
        if length == 0:
            break
        dest.write(data)
        if length < chunk_size:
            break
    dest.seek(0)
    return


