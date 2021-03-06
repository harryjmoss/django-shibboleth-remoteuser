from django.contrib import auth
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import ImproperlyConfigured

from shibboleth.app_settings import (
    SHIB_ATTRIBUTE_MAP, LOGOUT_SESSION_KEY, SHIB_REMOTE_USER_HEADER
)


class ShibbolethRemoteUserMiddleware(RemoteUserMiddleware):
    """
    Authentication Middleware for use with Shibboleth.
    Uses the recommended pattern for remote authentication from:
    http://code.djangoproject.com/svn/django/tags/releases/1.3/django/contrib/auth/middleware.py
    """
    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")

        # To support logout.  If this variable is True, do not
        # authenticate user and return now.
        if request.session.get(LOGOUT_SESSION_KEY) is True:
            return
        else:
            # Delete the shib reauth session key if present.
            request.session.pop(LOGOUT_SESSION_KEY, None)

        # Locate the remote user header.
        try:
            username = request.META[self.header]
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            #if request.user.is_authenticated:
            #    self._remove_invalid_user(request)
            #return
            return
        #If we got an empty value for request.META[self.header], treat it like
        #   self.header wasn't in self.META at all - it's still an anonymous user.
        if not username:
            return

        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if ((request.user.get_username() ==
                 self.clean_username(username, request))):
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)

        # Make sure we have all required Shibboleth elements before proceeding.
        shib_meta, error = self.parse_attributes(request)

        # Add parsed attributes to the session.
        request.session['shib'] = shib_meta
        if error:
            raise ShibbolethValidationError("All required Shibboleth elements"
                                            " not found.  %s" % shib_meta)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, remote_user=username, shib_meta=shib_meta)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)
            # call make profile.
            self.make_profile(user, shib_meta)
            # setup session.
            self.setup_session(request)

    def make_profile(self, user, shib_meta):
        """
        This is here as a stub to allow subclassing of
        ShibbolethRemoteUserMiddleware to include a make_profile method that
        will create a Django user profile from the Shib provided attributes
        By default it does nothing.
        """
        return

    def setup_session(self, request):
        """
        If you want to add custom code to setup user sessions, you
        can extend this.
        """
        return

    def parse_attributes(self, request):
        """
        Parse the incoming Shibboleth attributes.
        From: https://github.com/russell/django-shibboleth/blob/master/django_shibboleth/utils.py
        Pull the mapped attributes from the apache headers.
        """
        shib_attrs = {}
        error = False
        meta = request.META
        for header, attr in SHIB_ATTRIBUTE_MAP.items():
            required, name = attr
            value = meta.get(header, None)
            shib_attrs[name] = value
            if not value or value == '':
                if required:
                    error = True
        return shib_attrs, error


class ShibbolethValidationError(Exception):
    pass
