"""
Actor views for receiving information/changes from auth service and apply it on your service. All of methods are
could be used only if auth service sent this information.
"""
from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask import request

from flask.views import MethodView
from flask_babel import gettext as _
from flask_cors import cross_origin
from psycopg2 import sql

from .actions.actor_actions import CreateActorAction
from .actions.actor_actions import UpdateActorAction
from .actions.actor_actions import DeleteActorAction
from .actions.actor_actions import UpdateServiceSpecificAdminsAction

from .decorators import service_only
from .decorators import token_required
from .ecdsa_lib import verify_signature
from .service_view import SendCallback
from .utils import create_response_message
from .utils import get_current_actor
from .utils import json_dumps


class ActorMeView(MethodView):
    """
    @GET Get info about current actor@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    {
        "actor":
        {
            "uuid": "<uuid>",
            "actor_type": "classic_user",
            "created": "<datetime>",
            "initial_key": "<initial_key>",
            "root_perms_signature": "<root_perms_signature>",
            "secondary_keys": null,
            "uinfo": {
                "email": "<email>",
                "login": "<login>",
                "phone_number": "<phone_number>",
                "groups": ["<group_uuid>", "<group_uuid>"],
                "password": "<hashed_password>",
                "first_name": "<first_name>",
                "last_name": "<last_name>"
            },
            "root": false,
            "is_admin": false,
            "group_names": ["<group_name>", "<group_name>"]
        }
    }
    @
    """

    @token_required
    def get(self):
        actor = get_current_actor()

        group_uuids = actor.uinfo.get('groups')
        if group_uuids:
            query = """SELECT ARRAY(SELECT uinfo->>'group_name' FROM actor 
            WHERE uuid = ANY({}::uuid[]) AND actor_type = 'group') AS group_names"""
            appends_list = [sql.Placeholder('uuid_list')]
            values = dict(
                uuid_list=group_uuids
            )
            query = sql.SQL(query).format(*appends_list)
            group_names = app.db.fetchone(query, values)
            if group_names:
                group_names = group_names.get('group_names')
        else:
            group_names = list()
        
        if request.args.get('groups_only'):
            actor_dict = {'root': actor.root}
        else:
            actor_dict = actor.to_dict()
        actor_dict['is_admin'] = actor.is_admin
        actor_dict['group_names'] = group_names

        response = dict(
            actor=actor_dict,
        )
        return make_response(jsonify(response), 200)


class BaseActorView:

    @staticmethod
    def verify_request_data():
        data = request.json
        signature = data.pop("signature", None)
        if not data or not signature:
            response = create_response_message(message=_("Invalid request data."), error=True)
            return response, True

        if not verify_signature(app.config['AUTH_PUB_KEY'], signature, json_dumps(data, sort_keys=True)):
            response = create_response_message(message=_("Signature verification failed."), error=True)
            return response, True

        return data, False


    def get_callback_data(self, data):
        return {
            'sync_package_id': data.get('sync_package_id'),
            'object_uuid': data.get('object_uuid')
        }


class ActorView(MethodView, BaseActorView):
    """
    @POST Submodule Biom mode. Create actor based on request body, only for auth service@
    @POST_body_request
    {
        "actor": {
            "uinfo": {
                "email": "test54@gmail.com",
                "login": "test54",
                "phone_number": "+111111111111",
                "groups": ["4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"],
                "password": "ea82410c7a9991816b5eeeebe195e20a",
                "last_name": "test54",
                "first_name": "test54"
            },
            "actor_type": "classic_user"
        },
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "30450220210c63db563853d0d5a7037fa67bdab930a9b578b759ccfcd2a7acb7549c255d022100e1cc6d1fc707e9dac3b5782bae4334d5306ec37123425bb0415c65957d8f0b60"
    }
    @
    @POST_body_response
    {
        "message": "Actor was successfully created."
    }
    @
    @PUT Submodule Biom mode. Update actor partially based on request body, only for auth service@
    @PUT_body_request
    {
        "actors": [
            {
                "uuid": "036ccf1b-8ad6-4240-8c08-d7914b90aa2c",
                "uinfo": {
                    "email": "test54_new@gmail.com",
                    "login": "test54_new",
                    "phone_number": "+222222222222",
                    "groups": ["4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"],
                    "password": "ea82410c7a9991816b5ffffbe195e20a",
                    "last_name": "test54_new",
                    "first_name": "test54_new"
                },
                "actor_type": "classic_user"
            }
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "30440220720ca2ca14307e5c9340b830bf862581b7fe421841ca09ccbc52b9d7741d9f30022048ee0757fd37390c360d0253884a66913adef985ea244e99942142d684b591a9"
    }
    @
    @PUT_body_response
    {
        "message": "Actor was successfully updated."
    }
    @
    @DELETE Delete actor based on request body, only for auth service@
    @DELETE_body_request
    {
        "actor": {
                "uuid": "036ccf1b-8ad6-4240-8c08-d7914b90aa2c"
        },
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "3045022100ac7c12bc09bccf93c5e290db29e5b56bd0609bb6eb899802aa88624e47e23b5002206bdb22c7881b00f04f54302cab80ce53bdb80d775c65a990c09735b1c5bb3454"
    }
    @
    @DELETE_body_response
    {
        "message": "Actor was successfully deleted."
    }
    @
    """

    @service_only
    @cross_origin()
    def post(self):
        """
        Create actor. Only for auth service.
        @subm_flow Create actor. Only for auth service.
        """
        data, error = self.verify_request_data()
        actor = data.get("actor")
        if not error:
            response, status_code = CreateActorAction(actor).execute()
            if status_code == 200 or (response.get('error_message', '') == 'Such actor already exists locally'):
                SendCallback(action_type='create_actor', data=self.get_callback_data(data)).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    def put(self):
        """
        Update actor. Only for auth service.
        @subm_flow   Update actor. Only for auth service.
        """
        data, error = self.verify_request_data()
        if not error:
            response, status_code = UpdateActorAction(data=data).execute()
            if status_code == 200:
                SendCallback(action_type='update_actor', data=self.get_callback_data(data)).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    def delete(self):
        """
        Delete actor. Only for auth service
        @subm_flow Delete actor. Only for auth service
        """
        data, error = self.verify_request_data()
        if not error:
            response, status_code = DeleteActorAction(data=data).execute()
            if status_code == 200:
                SendCallback(action_type='delete_actor', data=self.get_callback_data(data)).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)


class ServiceSpecificAdminsView(MethodView, BaseActorView):
    """
    @PUT Submodule Biom mode. Update service specific admins list. Only for auth service@
    @PUT_body_request
    {
        "admins_data": [
            "036ccf1b-8ad6-4240-8c08-d7914b90aa2c",
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "object_uuid": "32ff9126-3e50-46ef-a45c-9c44faa9d537",
        "signature": "30440220720ca2ca14307e5c9340b830bf862581b7fe421841ca09ccbc52b9d7741d9f30022048ee0757fd37390c360d0253884a66913adef985ea244e99942142d684b591a9"
    }
    @
    @PUT_body_response
    {
        "message": "Admins list was successfully updated"
    }
    @
    """

    @service_only
    @cross_origin()
    def put(self):
        """
        Update service specific admins list. Only for auth service.
        @subm_flow Update service specific admins list. Only for auth service.
        """
        data, error = self.verify_request_data()
        admins_data = data.get("admins_data")
        if not error:
            response, status_code = UpdateServiceSpecificAdminsAction(app.config.get('SERVICE_UUID'), admins_data).execute()
            SendCallback(action_type='update_service_specific_admins_with_actor', data=self.get_callback_data(data)).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)
