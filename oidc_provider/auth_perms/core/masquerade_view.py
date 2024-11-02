from flask import request
from flask import jsonify
from flask import make_response
from flask import current_app as app
from flask.views import MethodView
from flask_cors import cross_origin

from .actions.masquerade_actions import MasqueradePermAction
from .perms.biom_level_chain import BiomLevelPermactionChain
from .utils import get_current_actor

class MasqueradeOn(MethodView):
    """
    @POST Use site as client@
    @POST_body_request
    {
        "actor_uuid": "1b2eac61-d704-425b-8d7e-988a55ce2b94"
    }
    @
    @POST_body_response
    {
        "masquerade_session": "01sst9WdmirxHfwZwlrjJuEUJZy6FwJR",
        "primary_session": "so58Yi0V172Saf7MV0hIOT6BL9XUVuEs"
    }
    @
    """
    @cross_origin()
    def post(self):
        data = request.json
        masquerade_uuid = data.get('actor_uuid')

        primary_session, masquerade_session = MasqueradePermAction(masquerade_uuid).execute()

        return make_response(jsonify(dict(
            primary_session=primary_session,
            masquerade_session=masquerade_session,
        )), 200)


class GetActorMasqueradingInfoView(MethodView):
    """ 
    @POST Get perms for masquerading actor@
    @POST_body_request
    Content-Type: None
    @
    @POST_body_response
    {
        "allowed": true,
        "masquerade_uuids_list": ["8e482f30-de28-4a5a-8e5e-4c525c72763d", "23d29947-b915-440c-8a89-9c0886247e81"]
    }
    @
    """
    @cross_origin()
    def post(self):
        actor = get_current_actor()
        response = {'allowed': False}

        if is_root := actor.is_root or actor.is_admin:
            response = {
                'allowed': True,
                'root' if is_root else 'admin': True
            }
        else:
            chain = BiomLevelPermactionChain(
                service_uuid=app.config.get('SERVICE_UUID'),
                user=actor,
                permaction_uuid=MasqueradePermAction.permaction_uuid(),
                source_class=MasqueradePermAction
            )
            permission = chain.get_permactions()

            if permission and permission.get("value"):
                if masquerade_uuids_list := permission.get('params', {}).get("masquerade", []):
                    response = {
                        'allowed': True,
                        'masquerade_uuids_list': masquerade_uuids_list
                    }
                
        return make_response(jsonify(response), 200)
