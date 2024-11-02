from flask_babel import gettext as _

DATABASE = {
    'ENGINE': 'postgresql',
    'NAME': '',
    'USER': '',
    'PASSWORD': '',
    'HOST': 'localhost'
}

SERVICE_NAME: str = ''

SERVICE_UUID: str = ''

SERVICE_PUBLIC_KEY: str = ''

SERVICE_PRIVATE_KEY: str = ''

SERVICE_DOMAIN: str = ''

PRIMARY_KEY_ONLY: bool = False

AUTH_STANDALONE: bool = False

DEFAULT_GROUP_NAME: str = "DEFAULT"

SESSION_STORAGE: str = "SESSION"

SSO_MODE: bool = False

BIOM_NAME: str = ''

REDIRECT_URL_AFTER_AUTHENTICATION: str = '/'

SKIP_SUBMODULE_ENDPOINTS: list = []

ORDERED_MIGRATIONS_DIRS: list = []

LANGUAGES_INFORMATION: list = [
    {
        "code": "en",
        "name": _("English")
    },
    {
        "code": "ru",
        "name": _("Russian")
    },
    {
        "code": "cn",
        "name": _("Chinese"),
        "block": True
    }
]

BANNED_WORDS_FOR_LOGIN: list = [] # iterable or string(splitlines() will be proceed)

AUTOADD_TO_SERVICE_LISTING_GROUP: bool = True

DEPENDED_SERVICES: dict = {}

DYNAMIC_DEPENDED_SERVICES_ENABLED: bool = False

DYNAMIC_DEPENDED_SERVICES: dict = {'': {}}

SESSION_TOKEN_LIFETIME_DAYS: int = 14

INTERNAL_USERS_AFTER_REGISTRATION: bool = False

INTERNAL_DOMAINS_ENABLED: bool = True

SHARED_MODEL_USAGE_ENABLED: bool = False 

GEVENT_CONNECTION_POOL_ENABLED: bool = False

ECOSYSTEM54_LOGGING_MODULE_ENABLED: bool = False