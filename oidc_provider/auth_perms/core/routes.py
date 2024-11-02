from . import auth_submodule
from .actor_view import ActorMeView
from .actor_view import ActorView
from .actor_view import ServiceSpecificAdminsView

from .auth_view import AboutView
from .auth_view import APT54View
from .auth_view import RegistrationView
from .auth_view import ClientAuthenticationView
from .auth_view import GetQRCodeView
from .auth_view import SaveSession
from .auth_view import GetSession
from .auth_view import RootAPT54View
from .auth_view import AuthorizationView
from .auth_view import AuthQRCodeAuthorizationView
from .auth_view import AuthSSOGenerationView
from .auth_view import AuthSSOAuthorizationView
from .auth_view import CreateSessionTokenByUuidView
from .admin_view import AdminView
from .admin_view import AdminActorView
from .admin_view import AdminActorsView
from .admin_view import AdminPermissionView
from .admin_view import AdminProfileView
from .invite_link_view import GetInviteLinkInfoView
from .masquerade_view import MasqueradeOn
from .masquerade_view import GetActorMasqueradingInfoView
from .permaction_view import ActorPermactionView
from .permaction_view import GroupPermactionView
from .synchronization_view import ProcessForcedSynchroniationDataView
from .synchronization_view import GetExistingUsersView
from .synchronization_view import SaveServicesCertificatesView
from .healthcheck_view import GetSynchronizationHashView
from .healthcheck_view import CheckServiceKeyPairView
from .healthcheck_view import CheckServiceCommunicationView
from .healthcheck_view import ResetServiceSessionsView
from .healthcheck_view import GetVersioningInfoView
from .public_interfaces_view import GetAllowedPublicInterfacesView
from .documentation_view import GetAPICallsDocumentationView
from .documentation_view import GetSyncDocumentationView


# Registration/authentication endpoints
auth_submodule.add_url_rule('/auth/', view_func=ClientAuthenticationView.as_view('auth'))  # Authentication
auth_submodule.add_url_rule('/reg/', view_func=RegistrationView.as_view('reg'))  # Registration
auth_submodule.add_url_rule('/authorization/', view_func=AuthorizationView.as_view('authorization'))  # Get template
auth_submodule.add_url_rule('/auth_qr_code/', view_func=AuthQRCodeAuthorizationView.as_view('auth_qr_login'))  # Login after qr scanning
auth_submodule.add_url_rule('/save_session/', view_func=SaveSession.as_view('save_session'))  # Save session in cookie
auth_submodule.add_url_rule('/get_session/', view_func=GetSession.as_view('get_session'))  # Get session with temporary session
auth_submodule.add_url_rule('/auth_sso_generation/', view_func=AuthSSOGenerationView.as_view('auth-sso'))  # Auth Single Sign-On generation
auth_submodule.add_url_rule('/auth_sso_login/', view_func=AuthSSOAuthorizationView.as_view('auth_sso_login'))  # Login after redirect from Auth service
auth_submodule.add_url_rule('/create_session_by_uuid/', view_func=CreateSessionTokenByUuidView.as_view('create_session_by_uuid'))  # Create session by uuid for admin masquerading
auth_submodule.add_url_rule('/apt54/', view_func=APT54View.as_view('apt54'))  # Get APT54
auth_submodule.add_url_rule('/apt54/root/', view_func=RootAPT54View.as_view('root_apt54'))  # Root APT54

# Auth API endpoints
auth_submodule.add_url_rule('/actor/', view_func=ActorView.as_view('actor'))  # CRUD actor from auth
auth_submodule.add_url_rule('/permaction/actor/',view_func=ActorPermactionView.as_view("actor_permaction")) # CRUD actor_permaction from auth
auth_submodule.add_url_rule('/permaction/group/',view_func=GroupPermactionView.as_view("group_permaction")) # CRUD group_permaction from auth
auth_submodule.add_url_rule('/specific_admins/update/', view_func=ServiceSpecificAdminsView.as_view('specific_admins'))
auth_submodule.add_url_rule('/synchronization/force/',view_func=ProcessForcedSynchroniationDataView.as_view("process_force_synchronization_data"))
auth_submodule.add_url_rule('/synchronization/get_existing_users/',view_func=GetExistingUsersView.as_view("synchronization_get_existing_users"))
auth_submodule.add_url_rule('/synchronization/certificates/',view_func=SaveServicesCertificatesView.as_view("synchronization_certificates"))

auth_submodule.add_url_rule('/healthcheck/get_hash/',view_func=GetSynchronizationHashView.as_view("get_synchronization_hash"))
auth_submodule.add_url_rule('/healthcheck/check_service_key_pair/',view_func=CheckServiceKeyPairView.as_view("check_service_key_pair"))
auth_submodule.add_url_rule('/healthcheck/check_service_communication/',view_func=CheckServiceCommunicationView.as_view("check_service_communication"))
auth_submodule.add_url_rule('/healthcheck/sessions_reset/',view_func=ResetServiceSessionsView.as_view("healthcheck_sessions_reset"))
auth_submodule.add_url_rule('/healthcheck/get_versioning_info/',view_func=GetVersioningInfoView.as_view("healthcheck_get_versioning_info"))

# Utility endpoints
auth_submodule.add_url_rule('/actor/me', view_func=ActorMeView.as_view('actor-me'))
auth_submodule.add_url_rule('/about/', view_func=AboutView.as_view('about'))  # Service/biom info
auth_submodule.add_url_rule('/get_qr_code/', view_func=GetQRCodeView.as_view('qr-code'))  # QR code generation
auth_submodule.add_url_rule('/get_public_interfaces/', view_func=GetAllowedPublicInterfacesView.as_view('allowed-public-interfaces'))

# Temporary endpoints
auth_submodule.add_url_rule('/get_invite_link_info/', view_func=GetInviteLinkInfoView.as_view('get_invite_link_info'))

# Admin panel in auth standalone
auth_submodule.add_url_rule('/auth_admin/', view_func=AdminView.as_view('admin'))
auth_submodule.add_url_rule('/auth_admin/profile/', view_func=AdminProfileView.as_view('admin_profile'))
auth_submodule.add_url_rule('/auth_admin/actors/', view_func=AdminActorsView.as_view('admin_actors'))
auth_submodule.add_url_rule('/auth_admin/actor/<uuid>/', view_func=AdminActorView.as_view('admin_actor'))
auth_submodule.add_url_rule('/auth_admin/permissions/', view_func=AdminPermissionView.as_view('admin_permissions'))

# Masquerade endpoint
auth_submodule.add_url_rule('/masquerade/on/', view_func=MasqueradeOn.as_view('masquerade_on'))
auth_submodule.add_url_rule('/masquerade/get_actor_info/', view_func=GetActorMasqueradingInfoView.as_view('masquerade_get_actor_info'))

# Documentation endpoints
auth_submodule.add_url_rule('/biom_documentation/api_calls/', view_func=GetAPICallsDocumentationView.as_view('get_api_calls'))
auth_submodule.add_url_rule('/biom_documentation/sync_classes/', view_func=GetSyncDocumentationView.as_view('get_sync_classes'))
