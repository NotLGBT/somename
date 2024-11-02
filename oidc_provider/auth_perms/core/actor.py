"""
Base actor class with manager. This class is used to get actor object like ORM. Usage:
Actor.objects.get(key=value) - get single actor by sent params
Actor.objects.filter(key=value) - get list of actors by sent kwargs arguments
Actor.objects.exists(key=value) - is actor with params sent in kwargs exists.
Actor.objects.get_by_session(session_token=session_token) - get by session token
"""

import json

import requests
from datetime import datetime
from flask import current_app as app
from psycopg2.extras import RealDictRow
from urllib.parse import urljoin
from flask_babel import gettext as _

from .exceptions import MultipleObjectsReturned
from .managers import BaseManager
from .utils import get_static_group
from .utils import get_auth_domain
from .utils import json_dumps
from .utils import get_language_header
from .utils import sign_data
from .utils import verify_signature
from .utils import check_if_auth_service


class ActorNotFound(Exception):

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            super().__init__(*args, *kwargs)
        else:
            message = 'No actor with such parameters found'
            super().__init__(message)


class ActorManager(BaseManager):

    def get(self, **kwargs):
        """
        Get Actors
        :return: [] or [Actor(actor) for actor in actors]
        @subm_flow
        """

        if not kwargs:
            raise ValueError('No filter parameters provided')

        query, values = self.compile_query(**kwargs)

        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            actor = cur.fetchall()

        if not actor:
            raise ActorNotFound

        if len(actor) > 1:
            raise MultipleObjectsReturned

        else:
            return Actor(actor[0])

    def filter(self, **kwargs):

        query, values = self.compile_query(**kwargs)

        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            actors = cur.fetchall()

        if not actors:
            return []

        else:
            return [Actor(actor) for actor in actors]

    def exists(self, **kwargs):

        query, values = self.exists_query(**kwargs)

        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            exists = cur.fetchone().get('exists')

        return exists

    @staticmethod
    def get_by_session(session_token=None):
        """
        Get actor by session token
        :param session_token:
        :return: Actor
        @subm_flow
        """

        if not session_token:
            raise ValueError('Invalid session_token')

        else:
            with app.db.get_cursor() as cur:
                cur.execute("SELECT A.* FROM actor A INNER JOIN service_session_token S ON S.uuid = A.uuid "
                            "WHERE S.session_token=%s", (session_token,))
                actor = cur.fetchone()

                if not actor:
                    raise ActorNotFound

                else:
                    return Actor(actor)


class Actor:

    objects = ActorManager(table_name='actor')

    def __init__(self, actor: RealDictRow):
        self.uuid = actor.get('uuid')
        self.actor_type = actor.get('actor_type')
        self.created = actor.get('created')
        self.initial_key = actor.get('initial_key')
        self.root_perms_signature = actor.get('root_perms_signature')
        self.secondary_keys = actor.get('secondary_keys')
        self.uinfo = actor.get('uinfo')
        self.root = self.is_root
        self._is_biom_admin = False
        self._is_specific_service_admin = False

    def __str__(self):
        return f'Actor of type {self.actor_type}'

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)

    def to_dict(self):
        return json.loads(json.dumps(self, default=lambda o: datetime.strftime(o, '%Y-%m-%d %H:%M:%S')
        if isinstance(o, datetime) else o.__dict__))

    def get_public_keys(self):
        """
        Get user ecdsa keys
        :return: initial ecdsa key, secondary ecdsa key
        """
        initial_key = self.initial_key.get('user_pub_key')
        secondary_keys = [key for key in self.secondary_keys.values()] if self.secondary_keys else list()

        return initial_key, secondary_keys

    def get_apt54(self):
        """
        Send POST request on auth for getting apt54
        :return: apt54
        """
        url = urljoin(get_auth_domain(internal=True), '/get_apt54/')

        data = dict()
        data['uuid'] = self.uuid
        data['service_uuid'] = app.config['SERVICE_UUID']
        data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'], json_dumps(data, sort_keys=True))

        response = requests.post(url, json=data, headers=get_language_header())

        if response.ok:
            data = json.loads(response.content)
            signature = data.get('signature')
            user_data = str(data.get('user_data')) + str(data.get('expiration'))

            if verify_signature(app.config['AUTH_PUB_KEY'], signature, user_data):
                return data

        return None

    def get_groups(self):
        """
        Get list of actor groups
        :return: list of groups
        """
        if self.actor_type in ('user', 'classic_user'):
            groups = self.uinfo.get('groups') if self.uinfo.get('groups') else []
            list_of_groups = [self.objects.get(uuid=group) for group in groups]
            return list_of_groups
        return []

    def get_actors(self):
        """
        Get list of group members
        :return: list of actors
        """
        if self.actor_type == 'group':
            query = """SELECT uuid, uinfo FROM actor WHERE %s in (SELECT jsonb_array_elements_text(uinfo->'groups'))"""
            values = [self.uuid]
            with app.db.get_cursor() as cur:
                cur.execute(query, values)
                users = [Actor(user) for user in cur.fetchall()]
            list_of_users = [self.objects.get(uuid=user.uuid) for user in users]
            return list_of_users
        return []

    @property
    def is_root(self):
        """
        Check if user root
        :return: True if root, False if not
        """
        if not self.root_perms_signature or not self.initial_key:
            return False

        if app.config.get('AUTH_STANDALONE'):
            if not verify_signature(app.config['SERVICE_PUBLIC_KEY'], self.root_perms_signature,
                                    self.uuid + self.initial_key):
                return False
        else:
            if not verify_signature(app.config['AUTH_PUB_KEY'], self.root_perms_signature,
                                    self.uuid + self.initial_key):
                return False

        return True

    @property
    def is_banned(self):
        """
        Check if user in BAN group
        :return: True if in BAN, False if not
        """
        ban_group_uuid = get_static_group('BAN')
        if not ban_group_uuid:
            # If someone delete BAN group so everyone in BAN
            # TODO: uncomment return True if need upper solution
            # return True
            return False

        ban_group_uuid = ban_group_uuid.get('uuid')
        if self.uinfo.get('groups'):
            if ban_group_uuid in self.uinfo.get('groups'):
                return True

        return False

    @property
    def is_admin(self):
        if self.is_biom_admin:
            self._is_biom_admin = True
            return True
        if not app.config.get('AUTH_STANDALONE') and not check_if_auth_service():
            self._is_specific_service_admin = self.is_specific_service_admin()
        return self._is_specific_service_admin

    @property
    def is_biom_admin(self):
        admin_group_uuid = get_static_group('ADMIN')
        if not admin_group_uuid:
            # If someone delete ADMIN group so there is no admins
            return False

        admin_group_uuid = admin_group_uuid.get('uuid')
        if self.uinfo.get('groups'):
            if admin_group_uuid in self.uinfo.get('groups'):
                return True

    def is_specific_service_admin(self, service_uuid=None):
        service_uuid = service_uuid or app.config.get('SERVICE_UUID')
        uuid_list = self.uinfo.get('groups', []) + [self.uuid]
        query = "SELECT EXISTS(SELECT 1 FROM service_specific_admins WHERE service_uuid=%s AND %s && admins_data)"
        return app.db.fetchone(query, [service_uuid, uuid_list]).get('exists')
