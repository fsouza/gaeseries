from django.contrib.auth.tests.auth_backends import BackendTest, RowlevelBackendTest, AnonymousUserBackendTest, NoAnonymousUserBackendTest
from django.contrib.auth.tests.basic import BASIC_TESTS
from django.contrib.auth.tests.decorators import LoginRequiredTestCase
from django.contrib.auth.tests.forms import FORM_TESTS
from django.contrib.auth.tests.remote_user \
        import RemoteUserTest, RemoteUserNoCreateTest, RemoteUserCustomTest
from django.contrib.auth.tests.models import ProfileTestCase
from django.contrib.auth.tests.tokens import TOKEN_GENERATOR_TESTS
from django.contrib.auth.tests.views \
        import PasswordResetTest, ChangePasswordTest, LoginTest, LogoutTest

# The password for the fixture data users is 'password'

__test__ = {
    'BASIC_TESTS': BASIC_TESTS,
    'FORM_TESTS': FORM_TESTS,
    'TOKEN_GENERATOR_TESTS': TOKEN_GENERATOR_TESTS,
}
