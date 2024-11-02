from flask import jsonify, request
from flask.views import MethodView
from typing import List

from flask_cors import cross_origin
from .decorators import data_parsing, service_only
from .utils import insert_or_update_group_permaction
from .utils import insert_or_update_actor_permaction
from .ecdsa_lib import verify_signature
from flask import current_app as app
from .utils import json_dumps
from flask_babel import gettext as _
from flask import make_response
from .service_view import SendCallback


def get_callback_data(data):
    return {
        'sync_package_id': data.get('sync_package_id'),
        'object_uuid': data.get('permactions')[0].get('actor_uuid')
    }


class ActorPermactionView(MethodView):
    """
    @POST Update permactions for user@
    @POST_body_request
    {
        "permactions": [
            {
                "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
                "actor_uuid": "c08c2ab3-934a-412c-9e5a-fd8afa4475ae",
                "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
                "value": 1,
                "params": {}
            }
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "3046022100e41c1ab2fd1b0efd177ca0ff6db9f900d4df634629a130e8479c6e413b543f1c022100d88c5e00ede4a29fca02a0d052124a26c7e6618dca147a4a6b8b37589aecc9da"
    }
    @
    @POST_body_response
    {
        "message": "Permactions successfully updated."
    }
    @
    @DELETE Delete permactions for user@
    @DELETE_body_request
    {
        "permactions": [
            {
                "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
                "actor_uuid": "c08c2ab3-934a-412c-9e5a-fd8afa4475ae",
                "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
            }
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "304502201658630080ecdd14b4a2babe353983a5a2b7c145dad7d7589f1042eeae276ba7022100e03ffedc3080e9dcd5b040c24a414819884669a402fb3db279cac6a325417921"
    }
    @
    @DELETE_body_response
    {
        "message": "Permactions successfully updated."
    }
    @
    """
    @service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
        Update permactions for user
        @subm_flow Update permactions for user
        """

        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            insert_or_update_actor_permaction(data.get("permactions"))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='create_actor_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    @data_parsing
    def delete(self, data, **kwargs):
        """
        Delete permactions for user
        @subm_flow Delete permactions for user
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            order = ["permaction_uuid", "actor_uuid", "service_uuid"]
            query, values = self.delete_permactions(
                order=order, permactions=data.get("permactions")
            )
            app.db.execute(query, tuple(values))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='delete_actor_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @staticmethod
    def delete_permactions(order, permactions):
        parts: List[str] = list()
        values: List = list()
        query = "DELETE FROM actor_permaction WHERE "
        for permaction in permactions:
            parts.append(f"({' AND '.join([f'{key}=%s' for key in order])})")
            values.extend([permaction.get(key) for key in order])
        query += " OR ".join(parts) + ";"
        return query, values

class GroupPermactionView(MethodView):
    """
    @POST Update permactions for group@
    @POST_body_request
    {
        "permactions": [
            {
                "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
                "actor_uuid": "cc2f6ce2-c473-4741-99f6-fd7aec45d073",
                "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
                "value": 1,
                "weight": 12,
                "params": {}
            }
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "3045022100c2410cf523c70549cdcd7b3cfdf397cf027fac8bdfae71651aa5718e4e103a0f02202d4cd2e517de75c842d392c37efac33cd7f37ab21a93be8af616d746100323fd"
    }
    @
    @POST_body_response
    {
        "message": "Permactions successfully updated."
    }
    @
    @DELETE Delete permactions for group@
    @DELETE_body_request
    {
        "permactions": [
            {
                "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
                "actor_uuid": "cc2f6ce2-c473-4741-99f6-fd7aec45d073",
                "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
            }
        ],
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "signature": "3045022100cef111311d30d0d5333a58680cdcd68055e6f5696a622f189c43cc8c8eb0ebd3022069884c92452a3edbd01b101be6fb1a3670f7f9f8ab578d63b1854048f22de4d5"
    }
    @
    @DELETE_body_response
    {
        "message": "Permactions successfully updated."
    }
    @
    """
    @service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
        Update permactions for group
        @subm_flow Update permactions for group
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400

        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            insert_or_update_group_permaction(data.get("permactions"))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='create_group_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    @data_parsing
    def delete(self, data, **kwargs):
        """
        Delete permactions for group
        @subm_flow Delete permactions for group
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            order = ["permaction_uuid", "actor_uuid", "service_uuid"]
            query, values = self.delete_permactions(
                order=order, permactions=data.get("permactions")
            )
            app.db.execute(query, tuple(values))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='delete_group_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @staticmethod
    def delete_permactions(order, permactions):
        parts: List[str] = list()
        values: List = list()
        query = "DELETE FROM group_permaction WHERE "
        for permaction in permactions:
            parts.append(f"({' AND '.join([f'{key}=%s' for key in order])})")
            values.extend([permaction.get(key) for key in order])
        query += " OR ".join(parts) + ";"
        return query, values
