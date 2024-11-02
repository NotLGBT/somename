AUTH_STANDALONE: bool = True
CONFIG_MODE = 'PRODUCTION'
REDIRECT_URL_AFTER_AUTHENTICATION = '/oidc/auth_code'



try:
    from local_settings import *
except ImportError:
    try:
        from local_settings import *
    except ImportError:
        pass
