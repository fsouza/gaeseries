# -*- coding: utf-8 -*-
"""
    flask.helpers
    ~~~~~~~~~~~~~

    Implements various helpers.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
import posixpath
import mimetypes
from time import time
from zlib import adler32

# try to load the best simplejson implementation available.  If JSON
# is not installed, we add a failing class.
json_available = True
json = None
try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            # Google Appengine offers simplejson via django
            from django.utils import simplejson as json
        except ImportError:
            json_available = False


from werkzeug import Headers, wrap_file, is_resource_modified, cached_property
from werkzeug.exceptions import NotFound

from jinja2 import FileSystemLoader

from .globals import session, _request_ctx_stack, current_app, request


def _assert_have_json():
    """Helper function that fails if JSON is unavailable."""
    if not json_available:
        raise RuntimeError('simplejson not installed')

# figure out if simplejson escapes slashes.  This behaviour was changed
# from one version to another without reason.
if not json_available or '\\/' not in json.dumps('/'):

    def _tojson_filter(*args, **kwargs):
        if __debug__:
            _assert_have_json()
        return json.dumps(*args, **kwargs).replace('/', '\\/')
else:
    _tojson_filter = json.dumps


def _endpoint_from_view_func(view_func):
    """Internal helper that returns the default endpoint for a given
    function.  This always is the function name.
    """
    assert view_func is not None, 'expected view func if endpoint ' \
                                  'is not provided.'
    return view_func.__name__


def jsonify(*args, **kwargs):
    """Creates a :class:`~flask.Response` with the JSON representation of
    the given arguments with an `application/json` mimetype.  The arguments
    to this function are the same as to the :class:`dict` constructor.

    Example usage::

        @app.route('/_get_current_user')
        def get_current_user():
            return jsonify(username=g.user.username,
                           email=g.user.email,
                           id=g.user.id)

    This will send a JSON response like this to the browser::

        {
            "username": "admin",
            "email": "admin@localhost",
            "id": 42
        }

    This requires Python 2.6 or an installed version of simplejson.  For
    security reasons only objects are supported toplevel.  For more
    information about this, have a look at :ref:`json-security`.

    .. versionadded:: 0.2
    """
    if __debug__:
        _assert_have_json()
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
        indent=None if request.is_xhr else 2), mimetype='application/json')


def make_response(*args):
    """Sometimes it is necessary to set additional headers in a view.  Because
    views do not have to return response objects but can return a value that
    is converted into a response object by Flask itself, it becomes tricky to
    add headers to it.  This function can be called instead of using a return
    and you will get a response object which you can use to attach headers.

    If view looked like this and you want to add a new header::

        def index():
            return render_template('index.html', foo=42)

    You can now do something like this::

        def index():
            response = make_response(render_template('index.html', foo=42))
            response.headers['X-Parachutes'] = 'parachutes are cool'
            return response

    This function accepts the very same arguments you can return from a
    view function.  This for example creates a response with a 404 error
    code::

        response = make_response(render_template('not_found.html'), 404)

    Internally this function does the following things:

    -   if no arguments are passed, it creates a new response argument
    -   if one argument is passed, :meth:`flask.Flask.make_response`
        is invoked with it.
    -   if more than one argument is passed, the arguments are passed
        to the :meth:`flask.Flask.make_response` function as tuple.

    .. versionadded:: 0.6
    """
    if not args:
        return current_app.response_class()
    if len(args) == 1:
        args = args[0]
    return current_app.make_response(args)


def url_for(endpoint, **values):
    """Generates a URL to the given endpoint with the method provided.
    The endpoint is relative to the active module if modules are in use.

    Here some examples:

    ==================== ======================= =============================
    Active Module        Target Endpoint         Target Function
    ==================== ======================= =============================
    `None`               ``'index'``             `index` of the application
    `None`               ``'.index'``            `index` of the application
    ``'admin'``          ``'index'``             `index` of the `admin` module
    any                  ``'.index'``            `index` of the application
    any                  ``'admin.index'``       `index` of the `admin` module
    ==================== ======================= =============================

    Variable arguments that are unknown to the target endpoint are appended
    to the generated URL as query arguments.

    For more information, head over to the :ref:`Quickstart <url-building>`.

    :param endpoint: the endpoint of the URL (name of the function)
    :param values: the variable arguments of the URL rule
    :param _external: if set to `True`, an absolute URL is generated.
    """
    ctx = _request_ctx_stack.top
    if '.' not in endpoint:
        mod = ctx.request.module
        if mod is not None:
            endpoint = mod + '.' + endpoint
    elif endpoint.startswith('.'):
        endpoint = endpoint[1:]
    external = values.pop('_external', False)
    return ctx.url_adapter.build(endpoint, values, force_external=external)


def get_template_attribute(template_name, attribute):
    """Loads a macro (or variable) a template exports.  This can be used to
    invoke a macro from within Python code.  If you for example have a
    template named `_cider.html` with the following contents:

    .. sourcecode:: html+jinja

       {% macro hello(name) %}Hello {{ name }}!{% endmacro %}

    You can access this from Python code like this::

        hello = get_template_attribute('_cider.html', 'hello')
        return hello('World')

    .. versionadded:: 0.2

    :param template_name: the name of the template
    :param attribute: the name of the variable of macro to acccess
    """
    return getattr(current_app.jinja_env.get_template(template_name).module,
                   attribute)


def flash(message, category='message'):
    """Flashes a message to the next request.  In order to remove the
    flashed message from the session and to display it to the user,
    the template has to call :func:`get_flashed_messages`.

    .. versionchanged: 0.3
       `category` parameter added.

    :param message: the message to be flashed.
    :param category: the category for the message.  The following values
                     are recommended: ``'message'`` for any kind of message,
                     ``'error'`` for errors, ``'info'`` for information
                     messages and ``'warning'`` for warnings.  However any
                     kind of string can be used as category.
    """
    session.setdefault('_flashes', []).append((category, message))


def get_flashed_messages(with_categories=False):
    """Pulls all flashed messages from the session and returns them.
    Further calls in the same request to the function will return
    the same messages.  By default just the messages are returned,
    but when `with_categories` is set to `True`, the return value will
    be a list of tuples in the form ``(category, message)`` instead.

    Example usage:

    .. sourcecode:: html+jinja

        {% for category, msg in get_flashed_messages(with_categories=true) %}
          <p class=flash-{{ category }}>{{ msg }}
        {% endfor %}

    .. versionchanged:: 0.3
       `with_categories` parameter added.

    :param with_categories: set to `True` to also receive categories.
    """
    flashes = _request_ctx_stack.top.flashes
    if flashes is None:
        _request_ctx_stack.top.flashes = flashes = session.pop('_flashes', [])
    if not with_categories:
        return [x[1] for x in flashes]
    return flashes


def send_file(filename_or_fp, mimetype=None, as_attachment=False,
              attachment_filename=None, add_etags=True,
              cache_timeout=60 * 60 * 12, conditional=False):
    """Sends the contents of a file to the client.  This will use the
    most efficient method available and configured.  By default it will
    try to use the WSGI server's file_wrapper support.  Alternatively
    you can set the application's :attr:`~Flask.use_x_sendfile` attribute
    to ``True`` to directly emit an `X-Sendfile` header.  This however
    requires support of the underlying webserver for `X-Sendfile`.

    By default it will try to guess the mimetype for you, but you can
    also explicitly provide one.  For extra security you probably want
    to sent certain files as attachment (HTML for instance).

    Please never pass filenames to this function from user sources without
    checking them first.  Something like this is usually sufficient to
    avoid security problems::

        if '..' in filename or filename.startswith('/'):
            abort(404)

    .. versionadded:: 0.2

    .. versionadded:: 0.5
       The `add_etags`, `cache_timeout` and `conditional` parameters were
       added.  The default behaviour is now to attach etags.

    :param filename_or_fp: the filename of the file to send.  This is
                           relative to the :attr:`~Flask.root_path` if a
                           relative path is specified.
                           Alternatively a file object might be provided
                           in which case `X-Sendfile` might not work and
                           fall back to the traditional method.
    :param mimetype: the mimetype of the file if provided, otherwise
                     auto detection happens.
    :param as_attachment: set to `True` if you want to send this file with
                          a ``Content-Disposition: attachment`` header.
    :param attachment_filename: the filename for the attachment if it
                                differs from the file's filename.
    :param add_etags: set to `False` to disable attaching of etags.
    :param conditional: set to `True` to enable conditional responses.
    :param cache_timeout: the timeout in seconds for the headers.
    """
    mtime = None
    if isinstance(filename_or_fp, basestring):
        filename = filename_or_fp
        file = None
    else:
        file = filename_or_fp
        filename = getattr(file, 'name', None)
    if filename is not None:
        if not os.path.isabs(filename):
            filename = os.path.join(current_app.root_path, filename)
    if mimetype is None and (filename or attachment_filename):
        mimetype = mimetypes.guess_type(filename or attachment_filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            if filename is None:
                raise TypeError('filename unavailable, required for '
                                'sending as attachment')
            attachment_filename = os.path.basename(filename)
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    if current_app.use_x_sendfile and filename:
        if file is not None:
            file.close()
        headers['X-Sendfile'] = filename
        data = None
    else:
        if file is None:
            file = open(filename, 'rb')
            mtime = os.path.getmtime(filename)
        data = wrap_file(request.environ, file)

    rv = current_app.response_class(data, mimetype=mimetype, headers=headers,
                                    direct_passthrough=True)

    # if we know the file modification date, we can store it as the
    # current time to better support conditional requests.  Werkzeug
    # as of 0.6.1 will override this value however in the conditional
    # response with the current time.  This will be fixed in Werkzeug
    # with a new release, however many WSGI servers will still emit
    # a separate date header.
    if mtime is not None:
        rv.date = int(mtime)

    rv.cache_control.public = True
    if cache_timeout:
        rv.cache_control.max_age = cache_timeout
        rv.expires = int(time() + cache_timeout)

    if add_etags and filename is not None:
        rv.set_etag('flask-%s-%s-%s' % (
            os.path.getmtime(filename),
            os.path.getsize(filename),
            adler32(filename) & 0xffffffff
        ))
        if conditional:
            rv = rv.make_conditional(request)
            # make sure we don't send x-sendfile for servers that
            # ignore the 304 status code for x-sendfile.
            if rv.status_code == 304:
                rv.headers.pop('x-sendfile', None)
    return rv


def send_from_directory(directory, filename, **options):
    """Send a file from a given directory with :func:`send_file`.  This
    is a secure way to quickly expose static files from an upload folder
    or something similar.

    Example usage::

        @app.route('/uploads/<path:filename>')
        def download_file(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER'],
                                       filename, as_attachment=True)

    .. admonition:: Sending files and Performance

       It is strongly recommended to activate either `X-Sendfile` support in
       your webserver or (if no authentication happens) to tell the webserver
       to serve files for the given path on its own without calling into the
       web application for improved performance.

    .. versionadded:: 0.5

    :param directory: the directory where all the files are stored.
    :param filename: the filename relative to that directory to
                     download.
    :param options: optional keyword arguments that are directly
                    forwarded to :func:`send_file`.
    """
    filename = posixpath.normpath(filename)
    if filename.startswith(('/', '../')):
        raise NotFound()
    filename = os.path.join(directory, filename)
    if not os.path.isfile(filename):
        raise NotFound()
    return send_file(filename, conditional=True, **options)


def _get_package_path(name):
    """Returns the path to a package or cwd if that cannot be found."""
    try:
        return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
    except (KeyError, AttributeError):
        return os.getcwd()


class _PackageBoundObject(object):

    def __init__(self, import_name):
        #: The name of the package or module.  Do not change this once
        #: it was set by the constructor.
        self.import_name = import_name

        #: Where is the app root located?
        self.root_path = _get_package_path(self.import_name)

    @property
    def has_static_folder(self):
        """This is `True` if the package bound object's container has a
        folder named ``'static'``.

        .. versionadded:: 0.5
        """
        return os.path.isdir(os.path.join(self.root_path, 'static'))

    @cached_property
    def jinja_loader(self):
        """The Jinja loader for this package bound object.

        .. versionadded:: 0.5
        """
        return FileSystemLoader(os.path.join(self.root_path, 'templates'))

    def send_static_file(self, filename):
        """Function used internally to send static files from the static
        folder to the browser.

        .. versionadded:: 0.5
        """
        return send_from_directory(os.path.join(self.root_path, 'static'),
                                   filename)

    def open_resource(self, resource):
        """Opens a resource from the application's resource folder.  To see
        how this works, consider the following folder structure::

            /myapplication.py
            /schemal.sql
            /static
                /style.css
            /templates
                /layout.html
                /index.html

        If you want to open the `schema.sql` file you would do the
        following::

            with app.open_resource('schema.sql') as f:
                contents = f.read()
                do_something_with(contents)

        :param resource: the name of the resource.  To access resources within
                         subfolders use forward slashes as separator.
        """
        return open(os.path.join(self.root_path, resource), 'rb')
