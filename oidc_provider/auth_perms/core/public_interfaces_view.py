import requests
from urllib.parse import urljoin

from flask import g
from flask import make_response
from flask import jsonify
from flask import current_app as app
from flask.views import MethodView
from flask_cors import cross_origin

from .decorators import token_required
from .ecdsa_lib import sign_data
from .utils import get_auth_domain
from .utils import json_dumps


class GetAllowedPublicInterfacesView(MethodView):
    """ 
    @GET Get public interface by permission@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    {
        "services": [
            {
                "icon_color": "ORANGE",
                "service_domain": https://example.com",
                "service_icon": "mdi-kangaroo",
                "service_name": "Example Service"
            },
            ...
        ]
    }
    @
    """

    @token_required
    @cross_origin()
    def get(self, **kwargs):
        self.actor = g.actor
        self.response = {'services': []}
        if self.actor.is_root or self.actor.is_biom_admin:
            self.get_for_admin()
        else:
            self.get_for_actor_groups()
        return make_response(jsonify(self.response), 200)
    
    def get_for_admin(self):
        # receiving all published interfaces from Auth service
        url = urljoin(get_auth_domain(internal=True), '/get_public_interfaces/service/')
        data = {
            'actor_uuid': self.actor.uuid,
            'service_uuid': app.config.get('SERVICE_UUID')
        }
        data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'],
                                        json_dumps(data, sort_keys=True))
        headers = {'content-type': 'application/json'}
        try:
            auth_response = requests.post(url, json=data, headers=headers)
            services = auth_response.json().get('services', [])
        except:
            pass
        else:
            self.response['services'] = services

    def get_for_actor_groups(self):
        # getting published interfaces from actor's group with the highest weight,
        # which has public_interfaces key
        query = """
            SELECT json_agg(PI) AS public_interfaces FROM actor A
            LEFT OUTER JOIN LATERAL 
            jsonb_array_elements(A.uinfo->'public_interfaces') PI(value) ON PI->>'display_service' = 'true'
            WHERE A.actor_type = 'group' AND A.uuid=ANY(%s::uuid[]) AND A.uinfo->>'public_interfaces' != '[]'
            GROUP BY A.uuid
            ORDER BY (A.uinfo->'weight')::bigint DESC LIMIT 1
        """
        result = app.db.fetchone(query, (self.actor.uinfo.get('groups', []),))
        if result:
            public_interfaces = result.get('public_interfaces')
            if public_interfaces and public_interfaces[0] is not None:
                self.response['services'] = public_interfaces
