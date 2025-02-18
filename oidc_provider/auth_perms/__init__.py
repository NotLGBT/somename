import os

from flask import Flask
from flask_babel import Babel
from flask_babel import gettext as _
from flask import g

from .core.actor import Actor
from .core.actor import ActorNotFound
from .core.exceptions import AuthPermsDataError
from .core.exceptions import BaseArgumentsError
from .core.managers import DatabaseManager
from .core.routes import auth_submodule as auth_submodule
from .core.utils import get_session_token

LOCALIZATION_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'localization')


class AuthPermsFlask(Flask):
    """
    This class need for replacing submodule blueprint endpoint view on any custom endpoint
    """

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """
        Remove url view from blueprints endpoint.
        """
        return super(AuthPermsFlask, self).add_url_rule(
            rule, endpoint, view_func, **options
        ) if not endpoint in self.config.get('SKIP_SUBMODULE_ENDPOINTS', []) else None


def set_actor():
    """
    Function that save actor in flask g.
    @subm_flow
    """
    session_token = get_session_token()
    if session_token and not hasattr(g, 'actor'):
        try:
            actor = Actor.objects.get_by_session(session_token=session_token)
        except ActorNotFound:
            return

        setattr(g, 'actor', actor)

    return


class AuthPerms:
    """
    Submodule configuration class. Needs to configure submodule variables and save it in correct places for usage in
    submodule.
    """

    def __init__(self, app, settings_module, config_mode='PRODUCTION', database_credentials=None,
                 database_credentials_dsn=None, is_manager=False, **kwargs):
        self.app = app
        self.config_mode = config_mode
        self.database_credentials = database_credentials
        self.database_credentials_dsn = database_credentials_dsn
        self.base_args = kwargs if not isinstance(kwargs, dict) else {}
        self.settings_module = settings_module
        self.is_manager = is_manager
        self.register_pybabel(app)

        self.parse_variables()
        self.configure_db(app=app)
        # Check if this is manager command
        if not self.table_exists(table_name='actor') or self.is_manager:
            self.set_base_args(app=app)
            return

        self.validate_base_args()
        self.set_base_args(app=app)
        self.app.register_blueprint(auth_submodule)
        self.set_before_request_functions(app=app)
        self.add_jinja_extensions(app=app)

    def parse_variables(self):
        """
        Parse variables from settings file with names which are in list.
        SERVICE_PRIVATE_KEY - service private key
        SERVICE_PUBLIC_KEY - service public key
        AUTH_PUB_KEY - auth service public key
        SERVICE_UUID - service uuid that could be received from auth database
        PRIMARY_KEY_ONLY - when there is actor signature verification, check signature with initial key only
        DEFAULT_GROUP_NAME - group name where service need to add actor after registration by default
        SESSION_STORAGE - place where session stores. Could be SESSION or HEADERS or None
        DATABASE - database credentials in dict
        DATABASE_URI - database URI
        BABEL_TRANSLATION_DIRECTORIES - directories where translations are stores
        BABEL_DEFAULT_LOCALE - default language code
        LANGUAGES - list of language codes which have translations
        LANGUAGE_COOKIE_KEY - cookie key where language code is stores
        LANGUAGES_INFORMATION - list of dicts with language information like name, code, block.
        DB_MINIMUM_CONNECTIONS - count of minimum connections in pool
        DB_MAXIMUM_CONNECTIONS - count of maximum connections in pool
        SERVICE_DOMAIN - current service full domain
        SERVICE_NAME - current service name
        AUTH_STANDALONE - enable standalone mode (False by default)
        DEPENDED_SERVICES - dict with service_name : service_domain where authentication is also needed
        DYNAMIC_DEPENDED_SERVICES_ENABLED - enable dynamic depended services mode according to HTTP_ORIGIN (may be front service) (False by default)
        DYNAMIC_DEPENDED_SERVICES - dict like {<front_domain>: {<back_service_name>: <back_service_domain>}}
        SESSION_TOKEN_LIFETIME_DAYS - override session_token expiration date; must be integer
        BANNED_WORDS_FOR_LOGIN - iterable or string(splitlines() will be proceed)
        AUTOADD_TO_SERVICE_LISTING_GROUP - enable automatic adding authenticated actor to service listing group (True by default)
        INTERNAL_USERS_AFTER_REGISTRATION - whether users will be internal when registering on current service
        INTERNAL_DOMAINS_ENABLED - enables usage of local network domains(or ip addresses)
        SHARED_MODEL_USAGE_ENABLED - enables applying of shared models migrations
        GEVENT_CONNECTION_POOL_ENABLED - enables usage of gevent friendly connection pool; must be used only with Gevent mode
        ECOSYSTEM54_LOGGING_MODULE_ENABLED - enables write logs 
        """
        for key in dir(self.settings_module):
            if key.isupper() and key in ['SERVICE_PRIVATE_KEY', 'SERVICE_PUBLIC_KEY', 'AUTH_PUB_KEY', 'SERVICE_UUID',
                                         'PRIMARY_KEY_ONLY', 'DEFAULT_GROUP_NAME', 'SESSION_STORAGE', 'DATABASE',
                                         'DATABASE_URI', 'BABEL_TRANSLATION_DIRECTORIES', 'BABEL_DEFAULT_LOCALE',
                                         'LANGUAGES', 'LANGUAGE_COOKIE_KEY', 'LANGUAGES_INFORMATION',
                                         'DB_MINIMUM_CONNECTIONS', 'DB_MAXIMUM_CONNECTIONS', 'REDIRECT_URL_AFTER_AUTHENTICATION',
                                         'SERVICE_DOMAIN', 'SERVICE_NAME', 'AUTH_STANDALONE', 'DEPENDED_SERVICES',
                                         'DYNAMIC_DEPENDED_SERVICES_ENABLED', 'DYNAMIC_DEPENDED_SERVICES', 'SESSION_TOKEN_LIFETIME_DAYS',
                                         'BANNED_WORDS_FOR_LOGIN', 'AUTOADD_TO_SERVICE_LISTING_GROUP', 'INTERNAL_USERS_AFTER_REGISTRATION',
                                         'INTERNAL_DOMAINS_ENABLED', 'SHARED_MODEL_USAGE_ENABLED', 'GEVENT_CONNECTION_POOL_ENABLED',
                                         'ECOSYSTEM54_LOGGING_MODULE_ENABLED']:
                self.base_args[key] = getattr(self.settings_module, key)

    def validate_base_args(self):
        """
        Validation of parsed variables
        """
        if not self.base_args.get('SERVICE_PRIVATE_KEY'):
            raise AuthPermsDataError('SERVICE_PRIVATE_KEY is required parameter for configuring auth permission part. '
                                     '\n SERVICE_PRIVATE_KEY - your service private key.')

        if not self.base_args.get('AUTH_STANDALONE'):
            if not self.base_args.get('AUTH_PUB_KEY'):
                raise AuthPermsDataError('AUTH_PUB_KEY is required parameter for configuring auth permission part. '
                                         '\n AUTH_PUB_KEY - auth public key where your service registered.')

        if not self.base_args.get('AUTH_STANDALONE'):
            query = """SELECT EXISTS(SELECT 1 FROM actor WHERE initial_key=%s)"""
            if not self.app.db.fetchone(query, [self.base_args.get('AUTH_PUB_KEY')]).get('exists'):
                raise AuthPermsDataError('Auth service is not registered in your database. \n Please register it.')

        if not self.base_args.get('SERVICE_UUID'):
            service_uuid = self.get_current_service_uuid()
            if not service_uuid:
                raise AuthPermsDataError('SERVICE_UUID or SERVICE_PUBLIC_KEY is required parameter for configuring '
                                         'auth permission part. \n If set SERVICE_PUBLIC_KEY you should add row with your '
                                         'service information in database.'
                                         '\n SERVICE_UUID - your service uuid that you received on the auth service during '
                                         'registration.')

            self.base_args['SERVICE_UUID'] = service_uuid

        query = """SELECT EXISTS(SELECT 1 FROM actor WHERE uuid=%s)"""
        if not self.app.db.fetchone(query, [self.base_args.get('SERVICE_UUID')]).get('exists'):
            raise AuthPermsDataError('Your service is not registered in your database. \n Please register it.')

        query = """SELECT EXISTS(SELECT 1 FROM actor WHERE actor_type='group' AND uinfo->>'group_name' = 'DEFAULT')"""
        if not self.app.db.fetchone(query).get('exists'):
            raise AuthPermsDataError('There is no DEFAULT group in your database. \n Please create it based on auth '
                                     'information.')

        query = """SELECT EXISTS(SELECT 1 FROM actor WHERE actor_type='group' AND uinfo->>'group_name' = 'ADMIN')"""
        if not self.app.db.fetchone(query).get('exists'):
            raise AuthPermsDataError('There is no ADMIN group in your database. \n Please create it based on auth '
                                     'information.')

        query = """SELECT EXISTS(SELECT 1 FROM actor WHERE actor_type='group' AND uinfo->>'group_name' = 'BAN')"""
        if not self.app.db.fetchone(query).get('exists'):
            raise AuthPermsDataError('There is no BAN group in your database. \n Please create it based on auth '
                                     'information.')

        if not self.base_args.get('PRIMARY_KEY_ONLY'):
            self.base_args['PRIMARY_KEY_ONLY'] = False

        if not self.base_args.get('DEFAULT_GROUP_NAME'):
            self.base_args['DEFAULT_GROUP_NAME'] = 'DEFAULT'

        if not self.base_args.get('DEPENDED_SERVICES'):
            self.base_args['DEPENDED_SERVICES'] = {}

        if not self.base_args.get('REDIRECT_URL_AFTER_AUTHENTICATION'):
            self.base_args['REDIRECT_URL_AFTER_AUTHENTICATION'] = "/"

        if not self.base_args.get('BABEL_DEFAULT_LOCALE'):
            self.base_args['BABEL_DEFAULT_LOCALE'] = 'en'

        if not self.base_args.get('AUTH_STANDALONE'):
            self.base_args['AUTH_STANDALONE'] = False

        if not self.base_args.get('LANGUAGES'):
            self.base_args['LANGUAGES'] = []

        if not self.base_args.get('LANGUAGE_COOKIE_KEY'):
            self.base_args['LANGUAGE_COOKIE_KEY'] = 'language'

        if not self.base_args.get('LANGUAGES_INFORMATION'):
            self.base_args['LANGUAGE_INFORMATION'] = []
            if self.base_args.get('LANGUAGES'):
                for code in self.base_args.get('LANGUAGES'):
                    if code == 'ru':
                        name = _('Russian')
                    elif code == 'cn':
                        name = _('Chinese')
                    elif code == 'en':
                        name = _('English')
                    else:
                        print('Unknown language code in LANGUAGES variable, please check it - %s. '
                              'Add language information in list LANGUAGES_INFORMATION in settings file like\n '
                              'LANGUAGES_INFORMATION=[{"code": "en", "name": "English"}, ...]' % code)
                        raise BaseArgumentsError(message="LANGUAGE_INFORMATION error. Unknown code.")

                    self.base_args['LANGUAGE_INFORMATION'].append({"code": code, "name": name})
        else:
            for language in self.base_args.get('LANGUAGES_INFORMATION'):
                if not language.get('code'):
                    print('There is no language code for %s.' % language)
                    raise BaseArgumentsError(message="LANGUAGE_INFORMATION code error.")

                if not language.get('name'):
                    print('There is no language name for %s.' % language)
                    raise BaseArgumentsError(message="LANGUAGE_INFORMATION name error.")

        if not self.base_args.get('DB_MINIMUM_CONNECTIONS'):
            self.base_args['DB_MINIMUM_CONNECTIONS'] = 1
        else:
            if not isinstance(self.base_args.get('DB_MINIMUM_CONNECTIONS'), int):
                try:
                    self.base_args['DB_MINIMUM_CONNECTIONS'] = int(self.base_args.get('DB_MINIMUM_CONNECTIONS'))
                except Exception as e:
                    self.base_args['DB_MINIMUM_CONNECTIONS'] = 1

        if not self.base_args.get('DB_MAXIMUM_CONNECTIONS'):
            self.base_args['DB_MAXIMUM_CONNECTIONS'] = 10
        else:
            if not isinstance(self.base_args.get('DB_MAXIMUM_CONNECTIONS'), int):
                try:
                    self.base_args['DB_MAXIMUM_CONNECTIONS'] = int(self.base_args.get('DB_MAXIMUM_CONNECTIONS'))
                except Exception as e:
                    self.base_args['DB_MAXIMUM_CONNECTIONS'] = 10

    def set_base_args(self, app):
        """
        Save parsed arguments in app config.
        """
        if not self.base_args.get('BABEL_TRANSLATION_DIRECTORIES') or LOCALIZATION_PATH not in \
                self.base_args.get('BABEL_TRANSLATION_DIRECTORIES'):
            if not self.base_args.get('BABEL_TRANSLATION_DIRECTORIES'):
                self.base_args['BABEL_TRANSLATION_DIRECTORIES'] = LOCALIZATION_PATH + ';'
            else:
                self.base_args['BABEL_TRANSLATION_DIRECTORIES'] += LOCALIZATION_PATH \
                    if self.base_args['BABEL_TRANSLATION_DIRECTORIES'].endswith(';') else ';' + LOCALIZATION_PATH + ';'

        if not self.base_args.get('SERVICE_UUID') and self.table_exists(table_name="actor"):
            self.base_args['SERVICE_UUID'] = self.get_current_service_uuid()

        app.config.update(self.base_args)

    def configure_db(self, app):
        """
        Configure database manager and add it as app attribute named db.
        """
        db_manager_config_data = {}
        if self.database_credentials:
            db_manager_config_data['database'] = self.database_credentials
        elif self.database_credentials_dsn:
            db_manager_config_data['dsn'] = self.database_credentials_dsn
        elif d := self.base_args.get('DATABASE'):
            db_manager_config_data['database'] = d
        elif d := self.base_args.get('DATABASE_URI'):
            db_manager_config_data['dsn'] = d
        else:
            raise AuthPermsDataError('There was no database information passed. You can pass in database_credentials '
                                     'dict with database information or database_credentials_dsn or DATABASE from '
                                     'kwargs or DATABASE_URI from kwargs.'
                                     '\n database_credentials - argument with database credentials in dict. '
                                     '\n database_credentials_dsn - argument with database credentials in string. '
                                     '\n DATABASE - kwargs argument with database credentials in dict. '
                                     '\n DATABASE_URI - kwargs argument with database credentials in string.')
        db_manager_config_data.update({
            'min_connections': self.base_args.get('DB_MINIMUM_CONNECTIONS', 1),
            'max_connections': self.base_args.get('DB_MAXIMUM_CONNECTIONS', 10),
            'use_gevent_pool': self.base_args.get('GEVENT_CONNECTION_POOL_ENABLED', False)
        })
        DatabaseManager(**db_manager_config_data).init_app(app)

        self.base_args.pop('DATABASE', None)
        self.base_args.pop('DATABASE_URI', None)

    def table_exists(self, table_name):
        """
        Check if table with received table_name exists in database.
        :param table_name: str. Required. Table name.
        :return: True or False.
        """
        query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables " \
                "WHERE table_schema='public' AND table_name=%s)"
        values = [table_name]
        return self.app.db.fetchone(query, values).get('exists')

    def get_current_service_uuid(self):
        """
        Get service uuid from database with SERVICE_PUBLIC_KEY variable. Searching in initial key or in secondary keys.
        :return: UUID or None.
        """
        if not self.base_args.get('SERVICE_PUBLIC_KEY'):
            return None

        query = """SELECT uuid AS uuid FROM actor WHERE actor_type='service' AND (initial_key=%s OR 
        %s = ANY(SELECT value FROM jsonb_each_text(secondary_keys))) LIMIT 1"""
        result = self.app.db.fetchone(query, [self.base_args.get('SERVICE_PUBLIC_KEY'),
                                              self.base_args.get('SERVICE_PUBLIC_KEY')])
        if not result:
            return None

        return result.get('uuid')

    @staticmethod
    def register_pybabel(app):
        """
        Initialize pybabel extension
        """
        Babel(app=app)

    @staticmethod
    def set_before_request_functions(app):
        """
        Create before request function for saving actor in g.
        """
        app.before_request(set_actor)

    @staticmethod
    def add_jinja_extensions(app):
        app.jinja_env.add_extension('jinja2.ext.do')
