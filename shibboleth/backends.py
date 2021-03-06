from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend


class ShibbolethRemoteUserBackend(RemoteUserBackend):
    """
    This backend is to be used in conjunction with the ``RemoteUserMiddleware`
    found in the middleware module of this package, and is used when the server
    is handling authentication outside of Django.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True
    User = get_user_model()
    def authenticate(self, request, remote_user, shib_meta):
        """
        The username passed as ``remote_user`` is considered trusted.  This
        method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """

        if not remote_user:
            return

        username = self.clean_username(remote_user)
        field_names = [x.name for x in self.User._meta.get_fields()]
        for field_name in field_names:
            shib_user_params = dict([(k, shib_meta[k]) for k in field_names if k in shib_meta])
        user = self.setup_user(request = request, username = username, defaults = shib_user_params)
        if user:
            self.update_user_params(user=user, params=shib_user_params)
            return user if self.user_can_authenticate(user) else None



    def setup_user(self, request, username, defaults):
        """
        This method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.
        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
          # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = self.User.objects.get_or_create(username=username, defaults=defaults)
            if created:
                user = self.handle_created_user(request, user)
        else:
            try:
                user = self.User.objects.get(username=username)
            except self.User.DoesNotExist:
                return
        return user


    def handle_created_user(self, request, user):
        """
        @note: setting password for user needs on initial creation of user instead of after auth.login() of middleware.
        because get_session_auth_hash() returns the salted_hmac value of salt and password.
        If it remains after the auth.login() it will return a different auth_hash
        than what's stored in session "request.session[HASH_SESSION_KEY]".
        Also we don't need to update the user's password everytime he logs in.
        """
        user.set_unusable_password()
        user.save()
        return self.configure_user(request, user)
    @staticmethod
    def update_user_params(user, params):
        """
        After receiving a valid user, we update the the user attributes according to the shibboleth
        parameters. Otherwise the parameters (like mail address, sure_name or last_name) will always
        be the initial values from the first login. Only save user object if there are any changes.
        """
        if len(params) > 0:
            if not min([getattr(user, k) == v for k, v in params.items()]):
                user.__dict__.update(**params)
                user.save()
