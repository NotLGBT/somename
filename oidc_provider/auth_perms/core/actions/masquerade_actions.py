
from flask import session
from flask import abort
from typing import Dict, List

from ..action import BasePermAction
from ..actor import ActorNotFound
from ..decorators import perms_check
from ..utils import logging_message
from ..utils import get_session_token
from ..utils import create_masquerading_session_token


class MasqueradePermAction(BasePermAction):
    
    @classmethod
    def permaction_uuid(cls) -> str:
        return "43204251-47fe-46c5-8277-e2ddac0451c4"

    @classmethod
    def permaction_type(cls) -> str:
        return "check"

    @classmethod
    def description(cls) -> str:
        return """
            This permaction allows to work
            as an another user.
            Example: {
                "masquerade": [
                    "903be7da-9f0a-4241-9d70-ba07cc858fed",
                    "03927f4a-ad8d-43d3-b2a6-a468cc6748f6"
                ]
            }
        """

    @classmethod
    def title(cls) -> str:
        return """
            Allow masquerading.
        """

    @classmethod
    def default_value(cls) -> int:
        return 0

    @classmethod
    def unions(cls) -> List[str]:
        return [
            "masquerade"
        ]

    @classmethod
    def params(cls) -> Dict:
        return {
            "masquerade": []
        }

    def __init__(self, masquerade_uuid: str):
        self.masquerade_uuid = masquerade_uuid

    @perms_check
    def execute(self):
        primary_session = get_session_token()
        try:
            masquerade_session = create_masquerading_session_token(self.masquerade_uuid)
        except (ValueError, ActorNotFound) as e:
            logging_message(e.args[0])
            abort(400)

        session['primary_session'] = primary_session
        session['session_token'] = masquerade_session
        return primary_session, masquerade_session

    def biom_perm(self, params: Dict):
        """
        Can use masquerade
        """
        result: bool = self.masquerade_uuid in params.get("masquerade", [])
        return result
