import json
import zipfile
from flask import request
from flask import jsonify
from flask import current_app as app
from flask import make_response
from flask.views import MethodView
from flask_cors import cross_origin

from .decorators import data_parsing
from .decorators import auth_service_only

from .utils import json_dumps
from .utils import check_if_auth_service
from .ecdsa_lib import verify_signature


class ProcessForcedSynchroniationDataView(MethodView):
    """
    @POST Force synchroniation@
    @POST_body_request
    {
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "forced_sync_mode": "full",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "message": "Success."
    }
    @
    """
    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        if check_if_auth_service():
            response = dict(message="Forced synchronization process is not available for Auth service.")
            status_code = 400

        elif data and verify_signature(
                app.config['AUTH_PUB_KEY'],
                data.pop("signature"),
                json_dumps(data, sort_keys=True)):

            if 'actors' in request.files:
                file = request.files.get('actors')
                data = self.get_data_from_zip(file)

                query = "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT(uuid) " \
                    "DO UPDATE SET root_perms_signature=EXCLUDED.root_perms_signature, initial_key=EXCLUDED.initial_key, secondary_keys = EXCLUDED.secondary_keys, uinfo=EXCLUDED.uinfo;"
                app.db.execute(query, [data.decode("utf-8")])
                
                response = dict(message="Success.")
                status_code = 200
            
            elif 'actors_uuids' in request.files:
                force_sync_modes = (
                    'full', 'groups_and_services_only',
                    'groups_only', 'services_only'
                )
                if (forced_sync_mode := data.get('forced_sync_mode', 'full')) in force_sync_modes:
                    data = self.get_data_from_zip(
                        request.files.get('actors_uuids')
                    )
                    actors_where_statement = self.get_actors_where_statement(forced_sync_mode)
                    delete_query =f"DELETE FROM actor WHERE {actors_where_statement}" + " AND NOT (uuid = ANY(%s::uuid[]))"
                    app.db.execute(delete_query, [json.loads(data.decode("utf-8"))])

                    response = dict(message="Success.")
                    status_code = 200
                else:
                    response = dict(message="Invalid forced sync mode value.")
                    status_code = 400

            elif 'actor_permactions' in request.files and 'group_permactions' in request.files and 'service_specific_admins' in request.files:
                
                def perms_sync(relation, data):
                    query = f"INSERT INTO {relation}_permaction SELECT * FROM jsonb_populate_recordset(null::{relation}_permaction, jsonb %s)"

                    delete_query = f"DELETE FROM {relation}_permaction"
                    app.db.execute(delete_query)
                    app.db.execute(
                        query, [data.decode("utf-8")]
                    )

                apa_data = self.get_data_from_zip(
                    request.files.get('actor_permactions')
                )
                perms_sync('actor', apa_data)

                gpa_data = self.get_data_from_zip(
                    request.files.get('group_permactions')
                )
                perms_sync('group', gpa_data)

                admins_file = request.files.get('service_specific_admins')
                admins_data = self.get_data_from_zip(admins_file)
                admins_query = "INSERT INTO service_specific_admins SELECT * FROM jsonb_populate_record(null::service_specific_admins, jsonb %s) ON CONFLICT(service_uuid) " \
                    "DO UPDATE SET admins_data=EXCLUDED.admins_data"
                app.db.execute(
                    admins_query, [admins_data.decode("utf-8")]
                )

                response = dict(message="Success.")
                status_code = 200
            else:
                response = dict(message="Invalid files data.")
                status_code = 400

        else:
            response = dict(message="Verify signature process failed.")
            status_code = 400
        return make_response(jsonify(response), status_code)


    def get_data_from_zip(self, zip_file):
        with zipfile.ZipFile(zip_file) as zip:
            with zip.open('auth_data.json') as jfile:
                return jfile.read()

    def get_actors_where_statement(self, forced_sync_mode):
        if forced_sync_mode == 'full':
            return "actor_type IN ('classic_user', 'user', 'group', 'service')"
        elif forced_sync_mode == 'groups_and_services_only':
            return "actor_type IN ('group', 'service')"
        elif forced_sync_mode == 'groups_only':
            return "actor_type = 'group'"
        elif forced_sync_mode == 'services_only':
            return "actor_type = 'service'"


class GetExistingUsersView(MethodView):
    """
    @POST Returns all existing actors with type user/classic_user, when Auth service sends this request@
    @POST_body_request
    {
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "users_list": [<uuid1>, <uuid2>, <uuid3>, ...]
    }
    @
    """
    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        if check_if_auth_service():
            response = dict(message="Not available for Auth service.")
            status_code = 400

        elif data and verify_signature(
                app.config['AUTH_PUB_KEY'],
                data.pop("signature"),
                json_dumps(data, sort_keys=True)):

            query = "SELECT json_agg(u.uuid) as users_list FROM (SELECT uuid FROM actor WHERE actor_type IN ('user', 'classic_user')) u"
            response = {
                'users_list': app.db.fetchone(query).get('users_list', [])
            }
            status_code = 200
        else:
            response = dict(message="Verify signature process failed.")
            status_code = 400
        return make_response(jsonify(response), status_code)


class SaveServicesCertificatesView(MethodView):
    """
    @POST Save services self signed certificates, when Auth service sends this data@
    @POST_body_request
    {
        "certificates": [
                {
                    "id": 5,
                    "service_uuid": "<service_uuid>",
                    "domains": "<service_domain>",
                    "certificate": "<certificate>",
                    "created": "<date>"
                }
            ],
        "service_uuid": "<auth_service_uuid>",
        "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
    }
    @
    @POST_body_response
    {
        "message": "Successfully synchronized."
    }
    @
    """
    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        if check_if_auth_service():
            response = dict(message="Not available for Auth service.")
            status_code = 400

        elif data and verify_signature(
                app.config['AUTH_PUB_KEY'],
                data.pop("signature"),
                json_dumps(data, sort_keys=True)):
            
            app.db.execute("DELETE FROM certificate")

            if certificates:= data.get('certificates'):
                app.db.execute(
                    "INSERT INTO certificate SELECT * FROM jsonb_populate_recordset(null::certificate, jsonb %s)",
                    (certificates,)
                )
            response = dict(message="Successfully synchronized.")
            status_code = 200
        else:
            response = dict(message="Verify signature process failed.")
            status_code = 400
        return make_response(jsonify(response), status_code)
