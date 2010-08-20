# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth
    ~~~~~~~~~~~~~~

    User authentication extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from google.appengine.api import users

from tipfy import abort, cached_property, import_string, redirect

try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError, e:
    pass

__version__ = '0.6.4'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: user_model
#:     A ``db.Model`` class used for authenticated users, as a string.
#:     Default is ``tipfy.ext.auth.model.User``.
#:
#: cookie_name
#:     Name of the autentication cookie. Default is ``tipfy.auth``.
#:
#: session_max_age
#:     Interval in seconds before a user session id is renewed.
#:     Default is 1 week.
default_config = {
    'user_model':      'tipfy.ext.auth.model.User',
    'cookie_name':     'tipfy.auth',
    'session_max_age': 86400 * 7,
}


class BaseAuth(object):
    auth_use_https = False

    @cached_property
    def auth_user_model(self):
        """Returns the configured user model.

        :returns:
            A :class:`tipfy.ext.auth.model.User` class.
        """
        return import_string(self.app.get_config(__name__, 'user_model'))

    def auth_login_url(self, redirect=None):
        """Returns a URL that, when visited, prompts the user to sign in.

        :param redirect:
            A full URL or relative path to redirect to after logging in.
        :returns:
            A URL to perform logout.
        """
        opts = {'continue': redirect or self.request.path}
        path = self.request.url_for('auth/login', **opts)
        if not self.app.dev and self.auth_use_https:
            return 'https://%s%s' % (self.request.host, path)

        return path

    def auth_logout_url(self, redirect=None):
        """Returns a URL that, when visited, logs out the user.

        :param redirect:
            A full URL or relative path to redirect to after logging out.
        :returns:
            A URL to perform logout.
        """
        opts = {'continue': redirect or self.request.path}
        path = self.request.url_for('auth/logout', **opts)
        if not self.app.dev and self.auth_use_https:
            return 'https://%s%s' % (self.request.host, path)

        return path

    def auth_signup_url(self, redirect=None):
        """Returns a URL that, when visited, prompts the user to sign up.

        :param redirect:
            A full URL or relative path to redirect to after sign up.
        :returns:
            A URL to perform logout.
        """
        opts = {'continue': redirect or self.request.path}
        path = self.request.url_for('auth/signup', **opts)
        if not self.app.dev and self.auth_use_https:
            return 'https://%s%s' % (self.request.host, path)

        return path

    def auth_create_user(self, username, auth_id, **kwargs):
        """Creates a new user entity.

        :param username:
            Unique username.
        :param auth_id:
            Unique authentication id. For App Engine users it is 'gae:user_id'.
        :returns:
            The new entity if the username is available, None otherwise.
        """
        return self.auth_user_model.create(username, auth_id, **kwargs)

    def auth_get_user_entity(self, username=None, auth_id=None):
        """Loads an user entity from datastore. Override this to implement
        a different loading method. This method will load the user depending
        on the way the user is being authenticated: for form authentication,
        username is used; for third party or App Engine authentication,
        auth_id is used.

        :param username:
            Unique username.
        :param auth_id:
            Unique authentication id.
        :returns:
            A ``User`` model instance, or None.
        """
        if auth_id:
            return self.auth_user_model.get_by_auth_id(auth_id)
        elif username:
            return self.auth_user_model.get_by_username(username)


class AppEngineAuthMixin(BaseAuth):
    """This RequestHandler mixin uses App Engine's built-in Users API. Main
    reasons to use it instead of Users API are:

    - You can use the decorator :func:`user_required` to require a user record
      stored in datastore after a user signs in.
    - It also adds a convenient access to current logged in user directly
      inside the handler, as well as the functions to generate auth-related
      URLs.
    - It standardizes how you create login, logout and signup URLs, and how
      you check for a logged in user and load an {{{User}}} entity. If you
      change to a different auth method later, these don't need to be
      changed in your code.
    """
    @cached_property
    def auth_session(self):
        """Returns the currently logged in user session. For app Engine auth,
        this corresponds to the `google.appengine.api.users.User` object.

        :returns:
            A `google.appengine.api.users.User` object if the user for the
            current request is logged in, or None.
        """
        return users.get_current_user()

    @cached_property
    def auth_current_user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        if not self.auth_session:
            return None

        # Load user entity.
        auth_id = 'gae|%s' % self.auth_session.user_id()
        return self.auth_get_user_entity(auth_id=auth_id)

    @cached_property
    def auth_is_admin(self):
        """Returns True if the current user is an admin.

        :returns:
            True if the user for the current request is an admin,
            False otherwise.
        """
        return users.is_current_user_admin()

    def auth_login_url(self, redirect=None):
        """Returns a URL that, when visited, prompts the user to sign in.

        :param redirect:
            A full URL or relative path to redirect to after logging in.
        :returns:
            A URL to perform logout.
        """
        return users.create_login_url(redirect or self.request.path)

    def auth_logout_url(self, redirect=None):
        """Returns a URL that, when visited, logs out the user.

        :param redirect:
            A full URL or relative path to redirect to after logging out.
        :returns:
            A URL to perform logout.
        """
        return users.create_logout_url(redirect or self.request.path)


class MultiAuthMixin(BaseAuth):
    """This RequestHandler mixin is used for custom or third party
    authentication. It requires a `SessionMixin` to be used with the handler
    as it depends on sessions to be set.
    """
    @cached_property
    def auth_session(self):
        """Returns the currently logged in user session. For multi auth,
        this corresponds to the auth session data, a dictionary-like object.

        :returns:
            A dictionary of auth session data if the user for the current
            request is logged in, or None.
        """
        cookie_name = self.app.get_config(__name__, 'cookie_name')
        return self.session_store.get_secure_cookie(cookie_name)

    @cached_property
    def auth_current_user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        # Get the authentication and session ids.
        auth_id = self.auth_session.get('id', None)
        session_id = self.auth_session.get('session_id', None)
        remember = self.auth_session.get('remember', '0')

        if auth_id is None:
            return None

        # Load user entity.
        user = self.auth_get_user_entity(auth_id=auth_id)
        if user is None:
            return None

        # Check if session matches.
        if not session_id or user.check_session(session_id) is not True:
            return None

        self.auth_set_session(user.auth_id, user.session_id, remember)
        return user

    @cached_property
    def auth_is_admin(self):
        """Returns True if the current user is an admin.

        :returns:
            True if the user for the current request is an admin,
            False otherwise.
        """
        if not self.auth_current_user:
            return False

        return self.auth_current_user.is_admin

    def auth_login_with_form(self, username, password, remember=False):
        """Authenticates the current user using data from a form.

        :param username:
            Username.
        :param password:
            Password.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            True if login was succesfull, False otherwise.
        """
        user = self.auth_get_user_entity(username=username)

        if user is not None and user.check_password(password) is True:
            # Successful login. Make the user available.
            self.auth_current_user = user
            # Store the cookie.
            self.auth_set_session(user.auth_id, user.session_id, remember)
            return True

        # Authentication failed.
        return False

    def auth_login_with_third_party(self, auth_id, remember=False, **kwargs):
        """Called to authenticate the user after a third party confirmed
        authentication.

        :param auth_id:
            Authentication id, generally a combination of service name and
            user identifier for the service, e.g.: 'twitter:john'.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            None. This always authenticates the user.
        """
        # Load user entity.
        user = self.auth_get_user_entity(auth_id=auth_id)
        if user:
            # Set current user from datastore.
            self.auth_set_session(user.auth_id, user.session_id, remember,
                **kwargs)
        else:
            # Simply set a session; user will be created later if required.
            self.auth_set_session(auth_id, remember=remember, **kwargs)

    def auth_set_session(self, auth_id, session_id=None, remember=False,
        **kwargs):
        """Sets or renews the auth session.

        :param auth_id:
            Authentication id, generally a combination of service name and
            user identifier for the service, e.g.: 'twitter:john'.
        :param session_id:
            A session identifier stored in the user entity, or None.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            None. This always authenticates the user.
        """
        remember = str(int(remember))

        if kwargs:
            self.auth_session.update(kwargs)

        self.auth_session.update({
            'id':         auth_id,
            'session_id': session_id,
            'remember':   remember,
        })

        cookie_args = {'session_expires': None}
        if remember == '0':
            # Non-persistent authentication (only lasts for a session).
            cookie_args['max_age'] = None
        else:
            cookie_args['max_age'] = self.app.get_config(__name__,
                'session_max_age')

        cookie_name = self.app.get_config(__name__, 'cookie_name')
        self.session_store.set_cookie(cookie_name, self.auth_session,
            **cookie_args)

    def auth_logout(self):
        """Logs out the current user. This deletes the authentication session.
        """
        self.auth_session.clear()
        cookie_name = self.app.get_config(__name__, 'cookie_name')
        self.session_store.delete_cookie(cookie_name)


class LoginRequiredMiddleware(object):
    """A RequestHandler middleware to require user authentication. This
    acts as a `login_required` decorator but for handler classes. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, LoginRequiredMiddleware

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           middleware = [LoginRequiredMiddleware]

           def get(self, **kwargs):
               return 'Only logged in users can see this.'
    """
    def pre_dispatch(self, handler):
        return _login_required(handler)


class UserRequiredMiddleware(object):
    """A RequestHandler middleware decorator to require the current user to
    have an account saved in datastore. This acts as a `user_required`
    decorator but for handler classes. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, UserRequiredMiddleware

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           middleware = [UserRequiredMiddleware]

           def get(self, **kwargs):
               return 'Only users can see this.'
    """
    def pre_dispatch(self, handler):
        return _user_required(handler)


class AdminRequiredMiddleware(object):
    """A RequestHandler middleware to require the current user to be admin.
    This acts as a `admin_required` decorator but for handler classes. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, AdminRequiredMiddleware

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           middleware = [AdminRequiredMiddleware]

           def get(self, **kwargs):
               return 'Only admins can see this.'
    """
    def pre_dispatch(self, handler):
        return _admin_required(handler)


def login_required(func):
    """A RequestHandler method decorator to require user authentication.
    Normally :func:`user_required` is used instead. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, login_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           @login_required
           def get(self, **kwargs):
               return 'Only logged in users can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _login_required(self) or func(self, *args, **kwargs)

    return decorated


def user_required(func):
    """A RequestHandler method decorator to require the current user to
    have an account saved in datastore. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, user_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           @user_required
           def get(self, **kwargs):
               return 'Only users can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _user_required(self) or func(self, *args, **kwargs)

    return decorated


def admin_required(func):
    """A RequestHandler method decorator to require the current user to be
    admin. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.ext.auth import AppEngineAuthMixin, admin_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           @admin_required
           def get(self, **kwargs):
               return 'Only admins can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _admin_required(self) or func(self, *args, **kwargs)

    return decorated


def _login_required(handler):
    """Implementation for login_required and LoginRequiredMiddleware."""
    if not handler.auth_session:
        return redirect(handler.auth_login_url())


def _user_required(handler):
    """Implementation for user_required and UserRequiredMiddleware."""
    if not handler.auth_session:
        return redirect(handler.auth_login_url())

    if not handler.auth_current_user:
        return redirect(handler.auth_signup_url())


def _admin_required(handler):
    """Implementation for admin_required and AdminRequiredMiddleware."""
    if not handler.auth_session:
        return redirect(handler.auth_login_url())

    if not handler.auth_is_admin:
        abort(403)
