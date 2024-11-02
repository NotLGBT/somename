from auth_perms.core.action import BasePermAction
from auth_perms.core.decorators import perms_check
from typing import Dict


class CanLoginInSynapse(BasePermAction):

    @perms_check
    def execute(self):
        pass

    @classmethod
    def title(cls) -> str:
        return "Allow to login in synapse"

    @classmethod
    def description(cls) -> str:
        return "PermAction allow to login in synapse"

    @classmethod
    def permaction_type(cls) -> str:
        return "simple"

    def biom_perm(self, params: Dict) -> bool:
        return True

    @classmethod
    def permaction_uuid(cls) -> str:
        return "70ef15f8-ab8e-4cf2-aaff-03c9fe3b462f"

    @classmethod
    def default_value(cls) -> int:
        return 0

    @classmethod
    def unions(cls) -> list[str]:
        return ["Synapse"]
