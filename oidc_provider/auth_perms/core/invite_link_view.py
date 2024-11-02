from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask import request
from flask.views import MethodView
from flask_babel import gettext as _

from .decorators import service_only
from .utils import create_response_message

"""
Unused functionality for registration by custom link and automatically adding in some group
"""


class GetInviteLinkInfoView(MethodView):
    """
    @POST Info about create invite link @
    @POST_body_request
    {
        "link_uuid": "68c27803-f8d4-4c8d-8dd5-3348f909f8f5",
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
    }
    @
    @POST_body_response
    {
        "identifier": {
            "actor": "66356f2e-987a-4031-af59-30a408f2fff5",
            "created": "Thu, 21 Apr 2022 10:31:28 GMT",
            "group_uuid": "e81081ae-5c10-4b69-b787-89d0ae0a271e",
            "identifier": null,
            "link": null,
            "params": null,
            "uuid": "68c27803-f8d4-4c8d-8dd5-3348f909f8f5"
        }
    }
    @
    """
    @service_only
    def post(self):
        """
        Info about create invite link
        @subm_flow
        """
        if not request.is_json:
            response = create_response_message(message=_("Invalid request type."), error=True)
            return make_response(jsonify(response), 422)

        data = request.json

        if not data.get('link_uuid', None):
            response = create_response_message(message=_("Invalid request data."), error=True)
            return make_response(jsonify(response), 400)

        with app.db.get_cursor() as cur:
            cur.execute("SELECT * FROM invite_link WHERE uuid = %s", (data.get('link_uuid'),))
            identifier = cur.fetchone()

        response = dict(
            identifier=identifier
        )
        return make_response(jsonify(response), 200)
