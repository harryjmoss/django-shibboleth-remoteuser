SECRET_KEY = 'xxxxxx'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'shibboleth',
)

AUTHENTICATION_BACKENDS = (
    'shibboleth.backends.ShibbolethRemoteUserBackend',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shibboleth.middleware.ShibbolethRemoteUserMiddleware',
)

SHIBBOLETH_ATTRIBUTE_MAP = {
   "Shib-Identity-Provider": (True, "idp"),
   "Shibboleth-mail": (True, "email"),
   "Shibboleth-eppn": (True, "username"),
   "Shibboleth-schoolStatus": (True, "status"),
   "Shibboleth-affiliation": (True, "affiliation"),
   "Shib-Session-ID": (True, "session_id"),
   "Shibboleth-givenName": (True, "first_name"),
   "Shibboleth-sn": (True, "last_name"),
   "Shibboleth-mail": (True, "email"),
   "Shibboleth-schoolBarCode": (False, "barcode")
}

SHIBBOLETH_LOGOUT_URL = 'https://sso.school.edu/logout?next=%s'
SHIBBOLETH_LOGOUT_REDIRECT_URL = 'http://school.edu/'


ROOT_URLCONF = 'shibboleth.urls'
