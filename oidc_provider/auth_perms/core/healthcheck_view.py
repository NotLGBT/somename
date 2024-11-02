import os

import warnings
from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask.views import MethodView
from flask_cors import cross_origin
from flask_babel import gettext as _
from werkzeug.exceptions import Forbidden

from .decorators import data_parsing
from .decorators import auth_service_only

from .actor import Actor
from .utils import json_dumps
from .utils import logging_message
from .utils import create_response_message
from .utils import check_if_auth_service
from .ecdsa_lib import verify_signature
from .ecdsa_lib import sign_data

from .service_view import BaseServiceCommunication


class GetSynchronizationHashView(MethodView):
    """
    @POST Request on getting a actor, group, permaction hash@
    @POST_body_request
    {
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "304402203f99c19cb807e87f3c9b1044c2a273adc8904a85a2686ec30d5e6c752b51dae1022014068244081d3baec473314b6ed06c73370a201f73f177d8e60699383c718bf6"
    }
    @
    @POST_body_response
    {
        "groups_hash": "cfc885490054763a8cd554eee0c7fa9e",
        "services_hash": "6218863cb7100f8becfebca0f20aa679",
        "permactions_hash_data": {
            "57aa1fd4-457d-433b-90a4-e573934efd7f": {
                "actor_permactions_hash": "0",
                "group_permactions_hash": "0"
            },
            "f05f50d6-1714-4124-bfc8-6093dd0892ef": {
                "actor_permactions_hash": "0",
                "group_permactions_hash": "0"
            }
        }
    }
    @
    """
    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
        @subm_flow Request on getting actor, groups, services and permactions hashes
        """
        self.is_auth_service = check_if_auth_service()
        if data and 'signature' in data and verify_signature(
                app.config.get('AUTH_PUB_KEY', 'SERVICE_PUBLIC_KEY'),
                data.pop("signature"),
                json_dumps(data, sort_keys=True)
            ):

            if actor_uuid := data.get('actor_uuid'):
                response = dict(
                    actor_hash=self.get_actor_hash(actor_uuid=actor_uuid)
                )
            else:
                response = dict(
                    groups_hash=self.get_actor_hash(actor_type='group'),
                    services_hash=self.get_actor_hash(actor_type='service'),
                    permactions_hash_data=self.get_permactions_hash_data(),
                    is_auth_service=self.is_auth_service
                )
            status_code = 200
        else:
            response = create_response_message(message="Receiving synchronization hashes failed.", error=True)
            status_code = 400
        return make_response(jsonify(response), status_code)

    def get_actor_hash(self, actor_type=None, actor_uuid=None):
        if actor_uuid:
            where_statement = "uuid = %s"
            values = (actor_uuid,)
        elif actor_type:
            where_statement = "actor_type = %s"
            values = (actor_type,)
        else:
            return '0'

        return app.db.fetchone(
                f"""
                SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS hash
                FROM (
                        SELECT uuid, uinfo
                        FROM actor
                        WHERE {where_statement}
                        ORDER BY uuid
                    ) AS t;
                """,
                values
            ).get('hash') or '0'

    def get_permactions_hash_data(self):
        if self.is_auth_service:
            result = dict()
            services = app.db.fetchall(
                f"""SELECT uuid from actor where actor_type='service' and uuid != '{app.config.get("SERVICE_UUID")}' """
            )
            base_query = """SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS hash
                 FROM (
                     SELECT permaction_uuid, params, actor_uuid, service_uuid, value
                     FROM {}_permaction
                     WHERE service_uuid = '{}'
                     ORDER BY permaction_uuid, actor_uuid
                 ) AS t;
                 """
            for service in services:
                result[service['uuid']] = {
                    'actor_permactions_hash': app.db.fetchone(base_query.format('actor', service['uuid'])).get('hash') or '0',
                    'group_permactions_hash': app.db.fetchone(base_query.format('group', service['uuid'])).get('hash') or '0'
                }
            return result
        else:
            base_query = """
                SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS hash
                FROM (
                    SELECT permaction_uuid, params, actor_uuid, service_uuid, value
                    FROM {}_permaction
                    ORDER BY permaction_uuid, actor_uuid
                ) AS t;
                """
            actor_permactions_hash = app.db.fetchone(
                base_query.format('actor')
            ).get("hash") or '0'
            group_permactions_hash = app.db.fetchone(
                base_query.format('group')
            ).get("hash") or '0'
            return dict(actor_permactions_hash=actor_permactions_hash, group_permactions_hash=group_permactions_hash)


class CheckServiceKeyPairView(MethodView):
    """
    @POST Check Service Key pair@
    @POST_body_request
    {
        "initial_key": "0421efc01a00dd8b46d7a819e1519f7f04a244e68f5c2f61019d766f34635f22d4964af7c58518e4150275e803360a714edd360f1bf2a25bb98b8dbd79479c7535",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "database": True,
        "settings": True,
        "valid_key_pair": True
    }
    @
    """
    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data):
        if data and 'signature' in data and verify_signature(
                app.config.get('AUTH_PUB_KEY', 'SERVICE_PUBLIC_KEY'),
                data.pop('signature'),
                json_dumps(data, sort_keys=True)
            ):
            # Get received from Auth public key
            public_key_from_auth = data.get('public_key', '')
            # Get public_key from db with service uuid
            database_public_key = app.db.fetchone(
                "SELECT initial_key FROM actor WHERE uuid=%s AND actor_type = 'service'",
                [app.config.get('SERVICE_UUID')]
            ).get('initial_key', '')
            # generate and verify signature with received public key and service private key
            check_data = json_dumps({'check_key': public_key_from_auth}, sort_keys=True)
            check_signature = sign_data(app.config.get('SERVICE_PRIVATE_KEY'), check_data)
            try:
                valid_key_pair = verify_signature(public_key_from_auth, check_signature, check_data)
            except:
                valid_key_pair = False

            response = {
                'database': public_key_from_auth == database_public_key,
                'settings': public_key_from_auth == app.config.get('SERVICE_PUBLIC_KEY'),
                'valid_key_pair': valid_key_pair
            }
            status_code = 200
        else:
            response, status_code = create_response_message(message="Signature verification failed.", error=True), 400
        return make_response(jsonify(response), status_code)


class HealthcheckAuthCommunication(BaseServiceCommunication):
    """
    Send test request on Auth service to checl is it possible
    """

    def __init__(self, data):
        super().__init__()
        self.endpoint = '/healthcheck/test_communication'
        self.data = data

    def execute(self):
        response = self.send_request(data=self.data, is_signed=False)
        if not response.ok:
            return None
        try:
            return response.json().get('message')
        except:
            return None


class CheckServiceCommunicationView(MethodView):
    """
    @POST Check Service Key pair@
    @POST_body_request
    {
        "service_uuid": "57aa1fd4-457d-433b-90a4-e573934efd7f",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "database": True,
        "settings": True,
        "valid_key_pair": True
    }
    @
    """
    @cross_origin()
    @data_parsing
    def post(self, data):
        status_code = 400
        if check_if_auth_service():
            message = "Unavailable for Auth service."
        elif data and 'signature' in data and verify_signature(
                app.config['AUTH_PUB_KEY'],
                data.pop('signature'),
                json_dumps(data, sort_keys=True)
            ):
            result = HealthcheckAuthCommunication(data).execute()
            if result:
                message = result
                status_code = 200
            else:
                message = "Service communication failed."
        else:
            message = "Signature verification failed."
        response = create_response_message(message=message, error=status_code==400)
        return make_response(jsonify(response), status_code)


class ResetServiceSessionsView(MethodView):
    """
    @POST Reset Service Sessions@
    @POST_body_request
    {
        "service_uuid": "57aa1fd4-457d-433b-90a4-e573934efd7f",
        "action": "for_service_as_actor" or "for_users" or "full_reset"
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "message" : 'Success'
    }
    @
    """
    @cross_origin()
    @data_parsing
    def post(self, data):
        if data and 'signature' in data and verify_signature(
                app.config.get('AUTH_PUB_KEY', 'SERVICE_PUBLIC_KEY'),
                data.pop('signature'),
                json_dumps(data, sort_keys=True)
            ):
            if (action := data.get('action')) in ('for_service_as_actor', 'for_users', 'full_reset'):
                query = "DELETE FROM service_session_token"
                if action == 'for_service_as_actor':
                    query += f" WHERE uuid = '{app.config.get('SERVICE_UUID')}'"
                elif action == 'for_users':
                    query += f""" WHERE service_uuid = '{app.config.get('SERVICE_UUID')}' AND session_token IN 
                    (SELECT session_token FROM service_session_token T JOIN actor A ON T.uuid = A.uuid WHERE A.actor_type IN ('user', 'classic_user'))"""
                try:
                    app.db.execute(query)
                except Exception as e:
                    logging_message(message=f'Error during session resetting: {e}')
                    response, status_code = create_response_message(message="An error has occured during sessions resetting", error=True), 400
                else:
                    if not check_if_auth_service():
                        logging_message(message='*'*50, level='info') # TODO delete?
                        logging_message(message=f'Resetting sessions alert. Action - {action}', level='info')
                        logging_message(message='*'*50, level='info')
                    response, status_code = create_response_message('Success'), 200
            else:
                response, status_code = create_response_message(message="Invalid request data.", error=True), 400
        else:
            response, status_code = create_response_message(message="Signature verification failed.", error=True), 400
        return make_response(jsonify(response), status_code)


class GetVersioningInfoView(MethodView):
    """
    @POST Get Service version info@
    @POST_body_request
    {
        "service_uuid": "57aa1fd4-457d-433b-90a4-e573934efd7f",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "service_uuid": "57aa1fd4-457d-433b-90a4-e573934efd7f",
        "version": 5.12.7.1,
        "description": "Current version short description"
    }
    @
    """
    @cross_origin()
    @data_parsing
    def post(self, data):
        status_code = 400
        message = "An error has occured during getting versioning information"
        service_actor = Actor.objects.get(uuid=data.get('service_uuid'))
        if service_actor and any((self.check_service_is_auth(service_actor), service_actor.is_admin)):
            if verify_signature(
                    service_actor.initial_key,
                    data.pop('signature'),
                    json_dumps(data, sort_keys=True)
                ):
                version, description = self.get_tag_name()
                if not version:
                    version, description = self.get_info()
                status_code = 200
            else:
                message = "Signature verification failed."
            if status_code == 200:
                response = {
                    'version': version or 'Not found',
                    'description': description or '',
                    'service_uuid': app.config.get('SERVICE_UUID')}
            else:
                response = create_response_message(message=message, error=True)
            return make_response(jsonify(response), status_code)
        else:
            raise Forbidden(_('Permissions denied.'))
    
    def check_service_is_auth(self, service: Actor) -> bool:
        """ 
        Check is request from auth service or not
        """
        return service.initial_key == app.config.get('AUTH_PUB_KEY')
    
    def get_tag_name(self) -> tuple[str, str]:
        """Get version from git-tag name if exists"""
        version, description = None, None
        import pygit2
        path = os.getcwd()
        repo = pygit2.Repository(path)
        try:
            version = repo.describe()
        except pygit2.GitError:
            version = None
        return version, description
    
    def get_info(self):
        version, description = None, None
        try:
            from service_version_info import version
        except ImportError:
            warnings.warn(
                'service_version_info.py file not found in root folder; versioning info cannot be received by Auth service'
            )
        else:
            try:
                from service_version_info import description
            except ImportError:
                warnings.warn("The 'description' variable is not defined inside service_version_info.py file")
        return version, description
