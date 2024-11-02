"""
Communication with other services as actor with session.
BaseServiceCommunication base class for getting session_token on target service and adding it in send_request
method. This is required for using functionality of some other service like usual actor.
"""
import json
import requests
from typing import Dict
from urllib.parse import urljoin
from collections import namedtuple

from flask import current_app as app
from flask_babel import gettext as _

from .actor import Actor
from .actions.actor_actions import CreateActorAction
from .actions.actor_actions import UpdateActorAction
from .actions.actor_actions import DeleteActorAction
from .ecdsa_lib import sign_data
from .exceptions import ServiceInvalidData
from .exceptions import ServiceIsNotActorError
from .exceptions import ServiceRequestError
from .exceptions import ServiceSaltError
from .exceptions import ServiceSessionError
from .utils import apt54_expired
from .utils import create_response_message
from .utils import get_service_certificate
from .utils import get_static_group
from .utils import hash_md5
from .utils import json_dumps
from .utils import logging_message


class BaseServiceCommunication:
    """
    Base class for service-service communication as actor.
    """

    def __init__(self, service=None, **kwargs):
        if service and not isinstance(service, Actor):
            raise ServiceIsNotActorError('Unknown service')
        self.endpoint = None
        self.method = 'post'
        self.internal_domains_enabled = kwargs.get(
            'internal_domains_enabled',
            app.config.get('INTERNAL_DOMAINS_ENABLED', True)
        )
        self.verify = True
        self._service_domain = None
        self._auth_service_domain = None

        if app.config.get('AUTH_STANDALONE'):
            self._standalone_init()
        else:
            auth_service = Actor.objects.get(initial_key=app.config['AUTH_PUB_KEY'])
            if self.internal_domains_enabled:
                self._auth_service_domain = auth_service.uinfo.get('internal_service_domain')
            if not self._auth_service_domain:
                self._auth_service_domain = auth_service.uinfo.get('service_domain')

            if service:
                self.service = service
                if self.internal_domains_enabled:
                    self._service_domain = service.uinfo.get('internal_service_domain')
                if not self._service_domain:
                    self._service_domain = service.uinfo.get('service_domain')
                self.verify = get_service_certificate(service.uuid, self._service_domain)
            else:
                self.service = auth_service
                self._service_domain = self._auth_service_domain

    def send_request(self, *args, **kwargs):
        if app.config.get('AUTH_STANDALONE'):
            result = self._execute_locally(*args, **kwargs)
        else:
            result = self._send_request(*args, **kwargs)
        return result

    def _send_request(self, data=None, custom_headers: dict = None, is_json: bool = True, is_signed: bool = True,
                     timeout: float = 10):
        """
        General function for sending request on service. Can be rewrite if you need
        :param data: dict. request data
        :param custom_headers: dict. Custom headers
        :param is_json: bool. Optional. If request not json.
        :param is_signed: bool. Optional. If no need service_uuid in request and data signing.
        Need for service_only decorator.
        :param timeout: integer. Optional. Request timeout.
        :return: response
        @subm_flow
        """
        if not self.endpoint:
            raise ServiceInvalidData

        if not data or not isinstance(data, dict):
            data = dict()

        session_token = self.get_session_token()

        headers = dict()
        headers['Session-Token'] = session_token
        headers['content-type'] = 'application/json'
        if custom_headers and isinstance(custom_headers, dict):
            headers.update(custom_headers)

        if is_signed:
            data.update(dict(
                service_uuid=app.config['SERVICE_UUID']
            ))
            data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'],
                                          json_dumps(data, sort_keys=True))

        url = urljoin(self._service_domain, self.endpoint)
        try:
            _method = getattr(requests, self.method.lower())
            if is_json:
                # Prepare json data with application json encoder
                data = json.loads(json.dumps(data, cls=app.json_encoder))
                response = _method(url, headers=headers, json=data, verify=self.verify, timeout=timeout)
            else:
                response = _method(url, headers=headers, data=data, verify=self.verify, timeout=timeout)
        except Exception as e:
            logging_message(message=e, status=500)
            raise ServiceRequestError

        return response

    def get_session_token(self):
        """
        Get session token from database.
        """
        session_token = app.db.fetchone("""SELECT session_token, apt54 FROM service_session_token WHERE uuid = %s 
        AND service_uuid = %s ORDER BY created DESC""", [app.config['SERVICE_UUID'], self.service.uuid])
        if session_token and not apt54_expired(session_token.get('apt54', {}).get('expiration')):
            return session_token.get('session_token')

        session_token = self.get_new_session_token()
        if not session_token:
            raise ServiceSessionError("Error with getting session")
        return session_token

    def get_new_session_token(self, repeatedly=False):
        self.current_service = Actor.objects.get(initial_key=app.config['SERVICE_PUBLIC_KEY'])
        url = urljoin(self._service_domain, '/auth/')

        # identification step
        request_data = {
            'step': 'identification',
            'uuid': app.config['SERVICE_UUID']
        }
        try:
            response = requests.post(url, json=request_data, verify=self.verify)
        except Exception as e:
            logging_message(f'Error with creation session at identification step.\nException - {e}', status=500)
            return
        if not response.ok:
            logging_message("Error with creation session at identification step.\n"
                  f"Response content - {response.content}", status=response.status_code)
            return
        salt = response.json().get('salt')
        if not salt:
            raise ServiceSaltError(message='Error with getting salt')

        # check secret step
        signed_salt = sign_data(app.config['SERVICE_PRIVATE_KEY'], salt)
        request_data.update({
            'step': 'check_secret',
            'signed_salt': signed_salt
        })
        try:
            response = requests.post(url, json=request_data, verify=self.verify)
        except Exception as e:
            logging_message(f'Error with creation session at check secret step.\nException - {e}', status=500)
            return
        if not response.ok:
            logging_message("Error with creation session at check secret step.\n"
                  f"Response content - {response.content}", status=response.status_code)
            return
        response_data = response.json()
        session_token = response_data.get('session_token')
        expiration = response_data.get('expiration')
        if not session_token or not expiration:
            logging_message("Error with creation session at check secret step.\n"
                  f"Invalid data was received: session_token - {session_saved}, expiration - {expiration}")
            return

        # save session step
        try:
            session_saved = self.save_session(session_token, expiration)
        except Exception as e:
            logging_message(f'Error with creation session.\n Exception - {e}', 500)
        else:
            if not session_saved and not repeatedly:
                return self.get_new_session_token(repeatedly=True)
            elif not session_saved and repeatedly:
                logging_message('Error with saving session_token for service because of dublicate value for a second time!')
        return session_token

    def save_session(self, session_token, expiration):
        """
        Save new session in database
        """
        user_data = json_dumps(self.current_service.to_dict(), sort_keys=True)
        # TODO: add signature?
        # signature = sign_data(app.config['SERVICE_PRIVATE_KEY'], user_data + expiration)
        apt54 = dict(
            user_data=json.loads(user_data),
            expiration=expiration,
        )
        query = "SELECT session_token, uuid FROM service_session_token WHERE session_token = %s"
        values = [session_token]
        existing_session_token = app.db.fetchone(query, values)
        if not existing_session_token:
            query = "INSERT INTO service_session_token(session_token, uuid, apt54, service_uuid) " \
                    "VALUES(%s, %s, %s::jsonb, %s)"
            values = [session_token, app.config['SERVICE_UUID'], json_dumps(apt54), self.service.uuid]

        elif existing_session_token.get('session_token') == session_token and \
                session_token.get('uuid') == app.config['SERVICE_UUID']:
            query = "UPDATE service_session_token SET apt54 = apt54 WHERE session_token= %s AND uuid = %s"
            values = [apt54, session_token, app.config['SERVICE_UUID']]
        else:
            # If such token already exists for another actor
            return False
        app.db.execute(query, values)
        return True

    def _standalone_init(self):
        self.service = None
        self.default_class = namedtuple(
            "MockClass",
            (
                "data",
                "execute",
            ),
            defaults=(
                None,
                lambda: {"error": True, "message": "You're in standalone mode."})
        )
        self._local_handlers = {
            "/create/actor": CreateActorAction,
            "/delete/actor": DeleteActorAction,
        }
        for url in ("/update/actor", "/update/actor/group", "/update/actor/ban", "/update/actor/login-value", "/update/actor/password", "/update/actor/update-uinfo-custom-fields"):
            self._local_handlers[url] = UpdateActorAction
    
    def prepare_data_for_standalone(self, data):
        return data

    def _execute_locally(self, data, *args, **kwargs):
        data = self.prepare_data_for_standalone(data)
        return self._local_handlers.get(self.endpoint, self.default_class)(data).execute()


class GetAndUpdateActor(BaseServiceCommunication):
    """
    Get and update locally actor by uuid or list of uuids. Use it if your service working locally and registered on some auth that is
    on some other server.
    """

    def __init__(self, uuid=None):
        super().__init__()
        self.endpoint = '/service/get_actor/'
        self.uuid = uuid
        self.data = dict()

    def update_actor(self):
        if self.uuid:
            self.data.update(uuid=self.uuid)

        response = self.send_request(data=self.data)
        if not response.ok:
            return None

        actors = json.loads(response.content).get('actors')
        if isinstance(actors, dict):
            query = "INSERT INTO actor SELECT * FROM jsonb_populate_record(null::actor, jsonb %s) ON CONFLICT(uuid) " \
                    "DO UPDATE SET initial_key=EXCLUDED.initial_key, uinfo=EXCLUDED.uinfo;"
        elif isinstance(actors, list):
            query = "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT(uuid) " \
                    "DO UPDATE SET initial_key=EXCLUDED.initial_key, uinfo=EXCLUDED.uinfo;"
        else:
            return None

        values = [json_dumps(actors)]
        app.db.execute(query, values)
        return actors


class GetAndUpdateGroups(BaseServiceCommunication):
    """
    Get and update locally actor(groups) by uuid. Use it if your service working locally and registered on some auth
    that is on some other server.
    """

    def __init__(self, data=None):
        super().__init__()
        self.endpoint = '/service/get_groups/'
        self.data = data if data else dict()

    def update_groups(self):
        data = dict(
            data=self.data
        )
        response = self.send_request(data=data)
        if not response.ok:
            return None

        actors = json.loads(response.content)
        if not actors:
            return None

        actors = actors.get('groups')
        query = "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT (uuid) " \
                "DO UPDATE SET uinfo = EXCLUDED.uinfo WHERE actor.uuid = EXCLUDED.uuid"
        values = [json_dumps(actors)]
        app.db.execute(query, values)
        if not self.data:
            # Need to delete groups that not in list. Cause we got all groups
            groups_uuid = [value.get('uuid') for value in actors]
            query = "DELETE FROM actor WHERE actor_type = 'group' AND NOT (uuid = ANY(%s::uuid[]))"
            values = [groups_uuid]
            app.db.execute(query, values)

        return actors


class SendCallback(BaseServiceCommunication):
    """
    Send callback request on auth service, that information was updated on your service.
    @subm_flow Send callback request on auth service, that information was updated on your service.
    """

    def __init__(self, action_type, data=None):
        super().__init__()
        self.action_type = action_type
        self.data = data if data and isinstance(data, dict) else dict()
        self.method = 'post'
        self.endpoint = '/service/callback/'

    def send_callback(self):
        """
            Send callback request on auth service, that information was updated on your service.
            @subm_flow Send callback request on auth service, that information was updated on your service.
            """
        self.data['action_type'] = self.action_type
        self.send_request(data=self.data, timeout=5)


class GetActorByLoginValue(BaseServiceCommunication):

    def __init__(self, login_type, login_value):
        super().__init__()
        self.method: str = 'post'
        self.endpoint: str = '/get/actors'
        self.data: Dict = {"uinfo": {login_type: login_value}}

    def execute(self) -> Dict:
        response: Dict = self.send_request(data=self.data, is_signed=False)
        if response.json().get("actors"):
            action = CreateActorAction(data=response.json().get("actors")[0])
            result = action.actor
            message, status_code = action.execute()
            if status_code != 200:
                result = message
        else:
            result = {"error": True, "message":_("Such actor does not exist")},
            status_code = 400
        return result, status_code


class CreateActor(BaseServiceCommunication):
    """
    Send request on auth service to create actor
    'Create actor' permaction must be allowed
    Only admins can create actors with type 'service' and 'user'
    @subm_flow
    """

    def __init__(self, uinfo: dict, actor_type: str = 'classic_user'):
        super().__init__()
        self.method = 'post'
        self.endpoint = '/create/actor'
        self.uinfo = uinfo
        self.actor_type = actor_type

    def execute(self):
        """
        Create actor
        @subm_flow
        """
        data = dict(
            uinfo=self.uinfo,
            actor_type=self.actor_type
        )
        response = self.send_request(data=data, is_signed=False)
        return response


class UpdateActor(BaseServiceCommunication):
    """
    Send request on auth service to update actor
    Admin only endpoint
    @subm_flow
    """

    def __init__(self, actor_uuid: str, uinfo: dict, actor_type: str = 'classic_user'):
        super().__init__()
        self.method = 'post'
        self.endpoint = '/update/actor'
        self.actor_uuid = actor_uuid
        self.uinfo = uinfo
        self.actor_type = actor_type

    def update_actor(self):
        """
        Update actor
        @subm_flow
        """
        if not Actor.objects.exists(uuid=self.actor_uuid):
            response = create_response_message(message="Error with updating user. There is no such actor.",
                                               error=True)
            return response

        data = dict(
            uuid=self.actor_uuid,
            uinfo=self.uinfo,
            actor_type=self.actor_type
        )
        response = self.send_request(data=data, is_signed=False)
        return response


class AddActorToOwnListingGroup(BaseServiceCommunication):
    """
    Service only endpoint
    """

    def __init__(self, actor_uuid):
        super().__init__()
        self.method: str = 'post'
        self.endpoint: str = '/update/actor/add-to-own-listing-group'
        self.data: Dict = {'actor_uuid': actor_uuid}

    def execute(self) -> Dict:
        response = self.send_request(data=self.data)
        return response


class UpdateActorGroups(BaseServiceCommunication):
    """
    Update actor groups info except ADMIN and BAN

    'Append group' permaction must be allowed

    params
        actor_uuid (group or actor)
        add_actors_list (actors list or groups list accordingly to actor_uuid)
        remove_actors_list (actors list or groups list accordingly to actor_uuid)
    """

    def __init__(self, actor_uuid, add_actors_list = [], remove_actors_list = []):
        super().__init__()
        self.method: str = 'post'
        self.endpoint: str = '/update/actor/group'
        self.data: Dict = {
            'uuid': actor_uuid,
            'add_actors_list': add_actors_list,
            'remove_actors_list': remove_actors_list
        }
    
    def execute(self) -> Dict:
        response = self.send_request(data=self.data, is_signed=False)
        return response
    
    def prepare_data_for_standalone(self, data):
        try:
            actor = Actor.objects.get(uuid=data['uuid'])
        except:
            return data
        else:
            groups = actor.uinfo.get('groups', [])
            for g in data['add_actors_list']:
                groups.append(g)
            for g in data['remove_actors_list']:
                if g in groups:
                    groups.remove(g)
            actor_data = actor.to_dict()
            actor_data['uinfo']['groups'] = groups
            return actor_data


class UpdateActorWithBanGroup(BaseServiceCommunication):
    """
    Add or remove actor from BAN group
    
    'Append to BAN group' permaction must be allowed

    params:
        actor_uuid
    """

    def __init__(self, actor_uuid):
        super().__init__()
        self.method: str = 'post'
        self.endpoint: str = '/update/actor/ban'
        self.data: Dict = {'uuid': actor_uuid}

    def execute(self) -> Dict:
        response = self.send_request(data=self.data, is_signed=False)
        return response
    
    def prepare_data_for_standalone(self, data):
        try:
            actor = Actor.objects.get(uuid=data['uuid'])
            ban_group = get_static_group('BAN')
            ban_uuid = ban_group['uuid']
        except:
            return data
        else:
            groups = actor.uinfo.get('groups', [])
            groups.append(ban_uuid) if ban_uuid not in groups else groups.remove(ban_uuid)
            actor_data = actor.to_dict()
            actor_data['uinfo']['groups'] = groups
            return actor_data


class UpdateActorLoginValue(BaseServiceCommunication):
    """
    Update actor email (for user/classic_user), 
    login/phone_number (only for classic_user)

    'Update actor email/login/phone number' permaction must be allowed
    NOTE: to change it for ADMIN actor service must be ADMIN too

    params:
        actor_uuid
        email
        login
        phone number
    """

    def __init__(self, actor_uuid, email=None, login=None, phone_number=None):
        super().__init__()
        self.method: str = 'post'
        self.endpoint: str = '/update/actor/login-value'
        self.data: Dict = {'uuid': actor_uuid}
        if email:
            self.data['email'] = email
        if login:
            self.data['login'] = login
        if phone_number:
            self.data['phone_number'] = phone_number
        

    def execute(self) -> Dict:
        response = self.send_request(data=self.data, is_signed=False)
        return response
    
    def prepare_data_for_standalone(self, data):
        try:
            actor = Actor.objects.get(uuid=data.pop('uuid'))
        except:
            return data
        else:
            actor_data = actor.to_dict()
            actor_data['uinfo'].update(data)
            return actor_data


class UpdateActorPassword(BaseServiceCommunication):
    """
    Send request on auth service to update password for classic_user

    'Update actor password' permaction must be allowed
    NOTE: to change it for ADMIN actor service must be ADMIN too

    params:
        actor_uuid
        new_password (unhashed, more than 4 characters)
    """

    def __init__(self, actor_uuid, new_password):
        super().__init__()
        self.method = 'post'
        self.endpoint = '/update/actor/password'
        self.new_password = new_password
        self.data: Dict = {'uuid': actor_uuid, 'password': hash_md5(new_password)}

    def execute(self):
        if len(self.new_password) >= 4:
            response = self.send_request(data=self.data, is_signed=False)
        else:
            return create_response_message("Password length too short. Minimum 4 characters", error=True), 400
        if isinstance(response, tuple):
            return response
        try:
            data = response.json()
        except:
            data = {'error': True, 'response_text': response.text}
        return data, response.status_code
    
    def prepare_data_for_standalone(self, data):
        try:
            actor = Actor.objects.get(uuid=data.pop('uuid'))
        except:
            return data
        else:
            actor_data = actor.to_dict()
            actor_data['uinfo']['password'] = self.new_password # will be hashed inside update action handlers
            return actor_data


class UpdateActorUinfoCustomFields(BaseServiceCommunication):
    """
    Update actor uinfo with any custom fields
    
    'Update actor uinfo custom fields' permaction must be allowed
    NOTE: to change it for ADMIN actor service must be ADMIN too
    
    params:
        actor_uuid
        uinfo dict with custom fields only (Nullable keys will be popped)
    """

    def __init__(self, actor_uuid, uinfo: Dict):
        super().__init__()
        self.method = 'post'
        self.endpoint = '/update/actor/update-uinfo-custom-fields'
        self.data: Dict = {'uuid': actor_uuid, 'uinfo': uinfo}

    def execute(self):
        response = self.send_request(data=self.data, is_signed=False)
        return response
    
    def prepare_data_for_standalone(self, data):
        try:
            actor = Actor.objects.get(uuid=data.pop('uuid'))
        except:
            return data
        else:
            actor_data = actor.to_dict()
            actor_data['uinfo'].update(data)
            return actor_data


class GetActorSessionOnServices(BaseServiceCommunication):
    """
    Service get session_tokens for actor on passed services

    Service must be ADMIN

    params:
        actor_uuid
        services_list (list with uuids)
    """

    def __init__(self, actor_uuid, services_list):
        super().__init__()
        self.method = 'post'
        self.endpoint = '/create_session_by_uuid/'
        self.services_list = services_list
        self.data: Dict = {'actor_uuid': actor_uuid}

    def execute(self):
        current_service = Actor.objects.get(uuid=app.config.get('SERVICE_UUID'))
        if not current_service.is_admin:
            return create_response_message("Service must be ADMIN", error=True), 403

        session_tokens = dict()
        for service_uuid in self.services_list:
            try:
                self.service = Actor.objects.get(uuid=service_uuid, actor_type='service')
                if self.internal_domains_enabled:
                    self._service_domain = self.service.uinfo.get('internal_service_domain', self.service.uinfo.get('service_domain'))
                else:
                    self._service_domain = self.service.uinfo.get('service_domain')
            except Exception as e:
                logging_message(f'Exception during getting service: {e}, service_uuid - {service_uuid}')
                continue

            try:
                service_response = self.send_request(data=self.data)
            except ServiceRequestError:
                continue

            if service_response.status_code == 200:
                session_tokens[self.service.uinfo['service_name'].capitalize()] = service_response.json().get('session_token')
            else:
                try:
                    error_message = service_response.json().get('error_message')
                except:
                    error_message = 'Server error'
                logging_message(f'Error during getting service: {error_message}, service_uuid - {service_uuid}', status=service_response.status_code)

        return session_tokens, 200
