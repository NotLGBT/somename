from flask import g
from flask import jsonify
from flask import make_response
from flask import current_app as app
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask.views import MethodView
from flask_cors import cross_origin

from werkzeug.exceptions import NotFound
from psycopg2 import errors

from .actor import Actor
from .actor import ActorNotFound
from .utils import get_current_actor
from .utils import create_response_message
from .decorators import admin_only
from .decorators import standalone_only
from .decorators import token_required
from .actions.actor_actions import CreateActorAction
from .actions.actor_actions import DeleteActorAction
from .actions.standalone_actions import UpdateProfileAction
from .actions.standalone_actions import UpdateActorAction
from .actions.permactions_actions import GetAllPermsAction
from .actions.permactions_actions import SetPermactionAction
from .actions.permactions_actions import DeletePermactionAction
from .actions.permactions_actions import UpdatePermactionAction


class AdminView(MethodView):
    """
    @GET Submodule Standalone. Redirect to page with profile info@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 11862
    Access-Control-Allow-Origin: *
    @
    @POST Submodule Standalone. Logout and redirect to home page@
    @POST_body_request
    {

    }
    @
    @POST_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 8488
    Access-Control-Allow-Origin: *
    @
    """

    @standalone_only
    @token_required
    @cross_origin()
    def get(self):
        """
        Redirect to page with profile info
        @subm_flow
        """
        return redirect(url_for('auth_submodule.admin_profile'))

    @standalone_only
    @token_required
    @cross_origin()
    def post(self):
        """
        Logout and redirect to home page
        @subm_flow
        """
        session.pop('session_token', None)
        response = make_response(redirect('/'))
        response.delete_cookie(app.config.get('SERVICE_NAME').capitalize())
        return response


class AdminActorsView(MethodView):
    """
    @GET Submodule Standalone. Get page with list of actors@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 28951
    Access-Control-Allow-Origin: *
    @
    @POST Submodule Standalone. Create a new actor based on request body@
    @POST_body_request
    {
        "uinfo": {
            "first_name": "test54",
            "last_name": "test54",
            "email": "test54@gmail.com",
            "login": "test54",
            "phone_number": "+111111111111",
            "password": "test54"
        },
        "actor_type": "classic_user"
    }
    @
    @POST_body_response
    {
        "message": "Actor was successfully created."
    }
    @
    @DELETE Submodule Standalone. Delete actor based on request body@
    @DELETE_body_request
    {
        "uuid": "d573cb16-ebc6-47d2-80a2-d5bd76493881"
    }
    @
    @DELETE_body_response
    {
        "message": "Actor was successfully deleted."
    }
    @
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def get(self):
        """
        Get page with list of actors
        @subm_flow  Get page with list of actors
        """
        actors = Actor.objects.filter()
        groups = Actor.objects.filter(actor_type='group')
        return render_template('admin_panel/actors.html', actors=actors, groups=groups)

    @standalone_only
    @admin_only
    @cross_origin()
    def post(self):
        """
               Create a new actor based on request body
               @subm_flow Create a new actor based on request body
               """
        if not request.is_json or not request.json.get('uinfo') or not request.json.get('actor_type'):
            response = create_response_message(message='Invalid request type', error=True)
            return make_response(jsonify(response), 400)
        actor = request.json
        response, status = CreateActorAction(actor).execute()
        return make_response(jsonify(response), status)

    @standalone_only
    @admin_only
    @cross_origin()
    def delete(self):
        """
        Delete actor based on request body
        @subm_flow  Delete actor based on request body
        """
        if not request.is_json or not request.json.get('uuid'):
            response = create_response_message(message='Invalid request type', error=True)
            return make_response(jsonify(response), 400)
        data = request.json
        actor = Actor.objects.get(uuid=data.get('uuid'))
        response, status = DeleteActorAction(actor.__dict__).execute()
        return make_response(jsonify(response), status)


class AdminActorView(MethodView):
    """
    @GET Submodule Standalone. Get page with actor detail based on uuid@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 87652
    Access-Control-Allow-Origin: *
    @
    @PUT Submodule Standalone. Update an actor partially based on uuid and request body@
    @PUT_body_request
    {
        "first_name": "test54_put",
        "last_name": "test54_put",
        "email": "test54_put@gmail.com",
        "birthday": null,
        "groups": ["dd909964-086c-4a81-8daf-34037c0bf544"],
        "password": "ea82410c7a9991816b5eeeebe195e20a"
    }
    @
    @PUT_body_response
    {
        "message": "Actor successfully updated"
    }
    @
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def get(self, uuid):
        """
        Get page with actor detail based on uuid
        @subm_flow
        """
        #TODO try catch for requests
        try:
            actor = Actor.objects.get(uuid=uuid)
        except ActorNotFound:
            raise NotFound('No actor with such UUID found')
        except errors.InvalidTextRepresentation:
            raise NotFound('Invalid UUID representation')

        uinfo = actor.uinfo
        if actor.actor_type in ['user', 'classic_user']:
            if actor.actor_type == 'classic_user':
                uinfo.pop('password')

        perms = GetAllPermsAction(actor.uuid).execute()
        actor_groups = {group.uuid: group for group in actor.get_groups()}
        groups = Actor.objects.filter(actor_type='group')
        actors = Actor.objects.filter()
        return render_template('admin_panel/actor.html', actor=actor, perms=perms,
                               actor_groups=actor_groups, groups=groups, actors=actors)

    @standalone_only
    @admin_only
    @cross_origin()
    def put(self, uuid):
        """
        Update an actor partially based on uuid and request body
        @subm_flow
        """
        data = request.json
        response, status_code = UpdateActorAction(data, uuid).execute()
        return make_response(jsonify(response), status_code)


class AdminProfileView(MethodView):
    """
    @GET Submodule Standalone. Get page with self admin profile info@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 11862
    Access-Control-Allow-Origin: *
    @
    @PUT Submodule Standalone. Update self admin profile partially based on request body@
    @PUT_body_request
    {
        "first_name": "qwerty",
        "last_name": "qwerty",
        "email": "qwerty@gmail.com",
        "birthday": null,
        "password": "qwerty"
    }
    @
    @PUT_body_response
    {
        "message": "Profile successfully updated"
    }
    @
    """
    @standalone_only
    @token_required
    @cross_origin()
    def get(self):
        """
        Get page with self admin profile info
        @subm_flow
        """
        actor = get_current_actor()
        actor_groups = {group.uuid: group for group in actor.get_groups()}
        if not hasattr(g, 'actor'):
            setattr(g, 'actor', actor)
        perms = GetAllPermsAction(actor.uuid).execute()
        return render_template('admin_panel/profile.html', perms=perms, actor_groups=actor_groups)

    @standalone_only
    @token_required
    @cross_origin()
    def put(self):
        """
        Update self admin profile partially based on request body
        @subm_flow
        """
        data = request.json
        response, status_code = UpdateProfileAction(data).execute()
        return make_response(jsonify(response), status_code)


class AdminPermissionView(MethodView):
    """
    @POST Submodule Standalone. Create permission@
    @POST_body_request
    {
        "perm_uuid": "6d0bed92-c745-4113-a431-f0dfd6262174",
        "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9",
        "value": 1,
        "params": {}
    }
    @
    @POST_body_response
    {
        "message": "Success"
    }
    @
    @PUT Submodule Standalone. Update permission@
    @PUT_body_request
    {
        "perm_uuid": "6d0bed92-c745-4113-a431-f0dfd6262174",
        "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9",
        "value": 0,
        "params": {}
    }
    @
    @PUT_body_response
    {
        "message": "Success"
    }
    @
    @DELETE Submodule Standalone. Delete permission@
    @DELETE_body_request
    {
        "perm_uuid": "66eff516-5404-469a-8cb0-bb38d9e25912",
        "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9"
    }
    @
    @DELETE_body_response
    {
        "message": "Success"
    }
    @
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def post(self):
        """
        Create permission
        @subm_flow
        """
        data = request.json
        response, status_code = SetPermactionAction(data).execute()
        return make_response(jsonify(response), status_code)

    @standalone_only
    @admin_only
    @cross_origin()
    def put(self):
        """
                Update permission
                @subm_flow
                """
        data = request.json
        response, status_code = UpdatePermactionAction(data).execute()
        return make_response(jsonify(response), status_code)

    @standalone_only
    @admin_only
    @cross_origin()
    def delete(self):
        """
                     Delete permission
                     @subm_flow
                     """
        data = request.json
        response, status_code = DeletePermactionAction(data).execute()
        return make_response(jsonify(response), status_code)
