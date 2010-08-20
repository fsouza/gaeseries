# -*- coding: utf-8 -*-
"""
    tipfy.ext.appstats
    ~~~~~~~~~~~~~~~~~~

    Sets up the appstats middleware. Can be used either in production or
    development.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.ext.appstats.recording import appstats_wsgi_middleware

__version__ = '0.6'
__version_info__ = tuple(int(n) for n in __version__.split('.'))


class AppstatsMiddleware(object):
    """A middleware that wraps the WSGI app to record appstats data.

    To enable it, add to config:

    .. code-block:: python

       config['tipfy'] = {
           'middleware': [
               'tipfy.ext.appstats.AppstatsMiddleware',
               # ...
           ]
       }
    """
    def post_make_app(self, app):
        """Wraps the application by App Engine's appstats.

        :param app:
            The WSGI application instance.
        :returns:
            The application, wrapped or not.
        """
        # Wrap the callable, so we keep a reference to the app...
        app.wsgi_app = appstats_wsgi_middleware(app.wsgi_app)
        # ...and return the original app.
        return app