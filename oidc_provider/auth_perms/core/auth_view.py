import base64
import json
import requests
import qrcode
from io import BytesIO
from psycopg2 import sql
from urllib.parse import urljoin

from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask.views import MethodView
from flask_babel import gettext as _
from flask_cors import cross_origin

from . import auth_submodule
from . import ERP_APP_URL
from .actor import ActorNotFound
from .decorators import admin_only
from .decorators import data_parsing
from .decorators import service_only
from .ecdsa_lib import sign_data
from .ecdsa_lib import verify_signature
from .exceptions import Auth54ValidationError
from .service_view import AddActorToOwnListingGroup
from .utils import actor_exists
from .utils import apt54_expired
from .utils import create_actor
from .utils import check_if_auth_service
from .utils import convert_datetime
from .utils import create_masquerading_session_token
from .utils import create_new_salt
from .utils import create_response_message
from .utils import create_session
from .utils import create_session_with_apt54
from .utils import create_temporary_session
from .utils import delete_temporary_session
from .utils import generate_qr_token
from .utils import get_apt54
from .utils import get_apt54_locally
from .utils import get_auth_domain
from .utils import get_default_user_group
from .utils import get_depended_services_source
from .utils import get_language_header
from .utils import get_public_key
from .utils import get_salt_from_depended_services
from .utils import get_service_locale
from .utils import get_session_token_by_auxiliary
from .utils import get_static_group
from .utils import get_user_salt
from .utils import hash_md5
from .utils import is_valid_uuid
from .utils import json_dumps
from .utils import logging_message
from .utils import request_actor_from_auth_service
from .utils import update_salt_data
from .utils import validate_email
from .utils import validate_login
from .utils import validate_phone_number
from .utils import logging_message
from ..settings_sample import LANGUAGES_INFORMATION


class BaseAuth(MethodView):

    @staticmethod
    def upgrade_salt_for(salt, actor_uuid, qr_token, salt_for='authentication'):
        app.db.execute("""UPDATE salt_temp SET salt_for = %s WHERE salt = %s AND uuid = %s AND qr_token = %s""",
                       [salt_for, salt, actor_uuid, qr_token])

    @staticmethod
    def parse_login_data(data):
        available_login_types = ('email', 'login', 'phone_number')
        login_types = []
        login_values = []
        for ltype in available_login_types:
            if data.get(ltype):
                login_types.append(ltype)
                login_values.append(data.get(ltype))
        return login_types, login_values

    @staticmethod
    def validate_login_value(login_type, login_value):
        login_value_is_valid = False
        invalid_msg = ""

        if login_type == 'email':
            try:
                validate_email(login_value)
            except Auth54ValidationError:
                invalid_msg = _("Email you have inputted is invalid. Please check it.")
            else:
                login_value_is_valid = True
        elif login_type == 'login':
            if validate_login(login_value):
                login_value_is_valid = True
            else:
                invalid_msg = _("Login you have inputted is invalid. Please check it. "
                "Login length must be from 3 to 36 and it must contain alphanumeric values, dots or underscores")
        else:
            if validate_phone_number(login_value):
                login_value_is_valid = True
            else:
                invalid_msg = _("Phone number you have inputted is invalid. Please check it.")

        return login_value_is_valid, invalid_msg

    @staticmethod
    def add_to_own_listing_group(actor_data):
        if app.config.get('AUTOADD_TO_SERVICE_LISTING_GROUP', True) and not actor_data['actor_type'] == 'service':
            service_uinfo = app.db.fetchone("SELECT uinfo FROM actor where initial_key = %s", [app.config.get('SERVICE_PUBLIC_KEY')])
            if service_uinfo and service_uinfo['uinfo'].get('listing_group'):
                actor_groups = actor_data['uinfo'].get('groups', [])
                if not service_uinfo['uinfo'].get('listing_group') in actor_groups:
                    try:
                        AddActorToOwnListingGroup(actor_uuid=actor_data['uuid']).execute()
                    except Exception as e:
                        logging_message(message=f'Error during adding actor to service listing group: {e}')


class RegistrationView(BaseAuth):
    """
    Registration with auth service
    @POST Registration user with auth service based on request body@
    @POST_body_request
    {
        "uinfo": {
            "first_name": "test421",
            "last_name": "test421"
        },
        "email": "test421@gmail.com",
        "login": "test421",
        "phone_number": "+111111111112",
        "password": "test421",
        "password_confirmation": "test421",
        "actor_type": "classic_user"
    }
    @
    @POST_body_response
    {
        "user": {
            "actor_type": "classic_user",
            "created": "Fri, 29 Apr 2022 10:44:50 GMT",
            "initial_key": null,
            "root_perms_signature": null,
            "secondary_keys": null,
            "uinfo": {
                "email": "test421@gmail.com",
                "first_name": "test421",
                "groups": [
                    "4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"
                ],
                "last_name": "test421",
                "login": "test421",
                "password": "6e8877bfa5e3c58f9de018d18ff823ef",
                "phone_number": "+111111111112"
            },
            "uuid": "7c71adbb-4cfe-4e91-b80e-9fcbc0de9812"
        }
    }
    @
    """

    @cross_origin()
    @data_parsing
    def post(self, **kwargs):
        """
        POST /reg/ endpoint
        @subm_flow POST /reg/ endpoint
        """
        data = kwargs.get('data')
        if not check_if_auth_service():
            if not app.config.get('AUTH_STANDALONE'):
                # Client service registration
                # Adding service default group in user info
                # Adding salt and service uuid in request data and signing data with service private key
                response, status = self.complete_service_registration(data=data)
                return make_response(jsonify(response), status)
        response, status = self.complete_auth_registration(data=data)

        return make_response(jsonify(response), status)


    def complete_service_registration(self, data):
        data = self.collect_data_for_auth(data, salt_for='registration')
        # Send request on auth service registration endpoint
        response = requests.post(urljoin(get_auth_domain(internal=True), '/reg/'), json=data,
                                 headers=get_language_header())
        # Response from auth
        if response.ok:
            response_data = response.json()
            user = response_data.pop('user')
            # Create user on client service with data from auth service
            try:
                query = "INSERT INTO actor SELECT * FROM jsonb_populate_record(null::actor, jsonb %s)"
                values = [json_dumps(user)]
                app.db.execute(query, values)
            except Exception as e:
                logging_message(message='Exception on creating user! %s' % e)
                logging_message(message="Error on creating user. core.auth_view.RegistrationView - POST.\n "
                                        "user - %s" % user)
                response = create_response_message(message=_("Some error occurred while actor registration. "
                                                             "Please contact the administrator."), error=True)

                return response, 400

            if data.get('actor_type') == 'classic_user':
                response = create_response_message(message=_("You are successfully registered."))
                response['uuid'] = user.get("uuid")
                response['user'] = user
                return response, 200

            content = json.loads(response.text)
            content['uuid'] = user.get('uuid')
            text = json_dumps(content)

            # Upgrade salt for using the same one in authentication
            salt = update_salt_data(user.get('uuid'), data.get('qr_token'))
            self.upgrade_salt_for(salt=salt.get('salt'), actor_uuid=salt.get('uuid'),
                                  qr_token=data.get('qr_token'), salt_for='authentication')
        else:
            text = response.text
        return json.loads(text), response.status_code


    def complete_auth_registration(self, data):
        if data.get('actor_type') == 'classic_user':
            response, status = self.registration_classic_user(data)
            return response, status

        # Registration user on auth service
        response, status = self.registration(data)

        if status == 200:
            salt = update_salt_data(response['user']['uuid'], data.get('qr_token'))
            # Update salt from registration to authentication for next step.
            if salt:
                self.upgrade_salt_for(salt=salt.get('salt'), actor_uuid=salt.get('uuid'),
                                      qr_token=data.get('qr_token'), salt_for='authentication')
            else:
                logging_message(message='Error with salt updating')

        return response, status


    def registration(self, data: dict):
        """
        Registration step two. In this step we check signed salt and if everything is good create user and return uuid
        :param data: dictionary with uuid and signed salt
        :return: response, status: response - dictionary with uuid of error=True flag with error message, status -
        http code
        Registration on auth service"
        @subm_flow Registration step two
        """
        signed_salt = data.get('signed_salt')
        pub_key = data.get('pub_key')
        qr_token = data.get('qr_token')
        if not pub_key or not signed_salt or not qr_token:
            # There is no public key or signed salt. Not full data set
            logging_message(message="Wrong data was sent. core.auth_view.RegistrationView - registration.\n "
                                    "pub_key - %s, signed_salt - %s, qr_token - %s" % (isinstance(pub_key, str),
                                                                                       isinstance(signed_salt, str),
                                                                                       isinstance(qr_token, str)))
            response = create_response_message(message=_("Invalid request data."), error=True)
            return response, 400

        # Check if request was sent from client service.
        if_from_client_service_result = self.check_if_from_client_service(data)
        if if_from_client_service_result.get('from_service'):
            if if_from_client_service_result.get('error'):
                if_from_client_service_result.pop('from_service')
                return if_from_client_service_result, 400

            salt = data.get('salt')
        else:
            salt = get_user_salt({'qr_token': qr_token}, salt_for='registration')

        if not salt:
            # There is no salt generated for that public key
            logging_message(message="There is no salt. core.auth_view.RegistrationView - registration.\n "
                                    "qr_token - %s, salt - %s" % (qr_token, salt))
            response = create_response_message(message=_("There is no verification data based on received data. \n "
                                                         "Please get new QR code."),
                                               error=True)
            return response, 400

        # Verify salt signature
        if not verify_signature(pub_key, signed_salt, salt):
            # Wrong signature verification
            logging_message(message="Signature verification failed. core.auth_view.RegistrationView - registration.\n")
            response = create_response_message(message=_("Signature verification failed."), error=True)
            return response, 400

        # Create secure uinfo
        uinfo = self.create_secure_uinfo(
            data,
            if_from_client_service_result.get('from_service'),
            if_from_client_service_result.pop('client_service_listing_group', None)
        )

        if uinfo.get('email'):
            if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM actor WHERE uinfo ->> 'email' = %s)""",
                               [uinfo.get('email')]).get('exists'):
                logging_message(message="User with such email already exists. core.auth_view. "
                                        "RegistrationView - registration.\n email - %s" % uinfo.get('email'))
                response = create_response_message(message=_("Actor with such email already exists."), error=True)
                return response, 400

            try:
                validate_email(uinfo.get('email'))
            except Auth54ValidationError as e:
                logging_message(message="Invalid email was inputed. core.auth_view. "
                                        "RegistrationView - registration.\n email - %s" % uinfo.get('email'))
                response = create_response_message(message=_("Email you have inputted is invalid. Please check it."),
                                                   error=True)
                return response, 400
        else:
            logging_message(message="User with has not input email. core.auth_view. "
                                    "RegistrationView - registration.\n uinfo - %s" % uinfo)
            response = create_response_message(message=_("There is no email in received data."), error=True)
            return response, 400

        # Creating user
        try:
            user = app.db.fetchone("""INSERT INTO actor(initial_key, uinfo) VALUES (%s, %s::jsonb) RETURNING *""",
                                   [pub_key, json_dumps(uinfo)])
            if user:
                user['created'] = convert_datetime(user['created'])
        except Exception as e:
            logging_message(message='Exception on creating user! RegistrationView - registration. \n Exception - %s' % e,
                            level='error')
            user = None

        if not user:
            # actor trigger returned None if such public_key already exists
            logging_message(message="Error with creating user. core.auth_view.RegistrationView - registration.\n "
                                    "pub_key - %s, uinfo - %s" % (pub_key, uinfo))
            response = create_response_message(message=_("Some error occurred while creating actor. "
                                                         "Please try again or contact the administrator"), error=True)
            return response, 400

        response = dict(
            user=user
        )
        if not if_from_client_service_result.get('from_service'):
            response['uuid'] = user.get('uuid')
        return response, 200

    def registration_classic_user(self, data: dict):
        """
        Classic registration with login/password.
        :param data: email or login or phone_number, password, password_confirmation
        :return: response, status: response - dictionary with created user or error=True flag with error message,
        status - http code
        @subm_flow Classic registration with login/password
        """
        login_types, login_values = self.parse_login_data(data)

        # Check base arguments
        if not login_values or not all(login_values) or not data.get('password') or not data.get('password_confirmation'):
            logging_message(message="Wrong data. core.auth_view.RegistrationView - registration_classic_user.\n "
                                    "types is %s, values is %s, password - %s, "
                                    "password_confirmation - %s" % (login_types, login_values,
                                                                    isinstance(data.get('password'), str),
                                                                    isinstance(data.get('password_confirmation'), str)))
            response = create_response_message(message=_("Invalid request data."), error=True)
            return response, 400

        # Verify signature from client service
        if_from_client_service_result = self.check_if_from_client_service(data)
        if if_from_client_service_result.get('from_service'):
            if if_from_client_service_result.get('error'):
                if_from_client_service_result.pop('from_service')
                return if_from_client_service_result, 400

        # Check password
        password = data.get('password')
        password_confirmation = data.get('password_confirmation')
        if len(password) < 4:
            response = create_response_message(message=_("Password length too short. Minimum 4 characters"), error=True)
            return response, 400
        elif password != password_confirmation:
            logging_message(message="Password and password confirmation do not match. "
                                    "core.auth_view.RegistrationView - registration_classic_user. ")
            response = create_response_message(message=_("Password and password confirmation do not match. "
                                                         "Please check it."), error=True)
            return response, 400
        
        # Validate and check unique login values
        for login_type, login_value in zip(login_types, login_values):
            login_value_is_valid, invalid_msg = self.validate_login_value(login_type, login_value)
            if not login_value_is_valid:
                response = create_response_message(message=invalid_msg, error=True)
                return response, 400

            if app.db.fetchone("SELECT EXISTS(SELECT 1 FROM actor WHERE uinfo->>%s = %s "
                            "AND actor_type = ANY(ARRAY['classic_user', 'user']))", [login_type, login_value]).get('exists'):
                logging_message(message=f"User with such {login_type} exists. "
                                        f"core.auth_view.RegistrationView - registration_classic_user.\n {login_type} - {login_value}")
                # because of translations
                if login_type == 'email':
                    msg = _("Actor with such email already exists")
                elif login_type == 'login':
                    msg = _("Actor with such login already exists")
                else:
                    msg = _("Actor with such phone number already exists")
                response = create_response_message(message=msg, error=True)
                return response, 400

        # Validate accepted uinfo
        uinfo = data.get('uinfo')
        if uinfo:
            if not isinstance(uinfo, dict):
                logging_message(message="Uinfo is not a dict. "
                                        "core.auth_view.RegistrationView - registration_classic_user.\n"
                                        "uinfo type - %s" % type(uinfo))
                response = create_response_message(message=_("Invalid request data type."), error=True)
                return response, 400
            if any(login_type in uinfo for login_type in login_types):
                logging_message(message=f"Some of {login_types} is in uinfo .core.auth_view.RegistrationView - registration_classic_user")
                response = create_response_message(
                    message=_("Invalid parameter for login in optional data."),
                    error=True
                )
                return response, 400
            if 'password' in uinfo:
                logging_message(message="Password is in uinfo. "
                                        "core.auth_view.RegistrationView - registration_classic_user")
                response = create_response_message(
                    message=_("Invalid parameter password in optional data."),
                    error=True
                )
                return response, 400
        
        # Create secure uinfo
        uinfo = self.create_secure_uinfo(
            data,
            if_from_client_service_result.get('from_service'),
            if_from_client_service_result.pop('client_service_listing_group', None)
        )

        # Parse and add login values to uinfo
        for login_type, login_value in zip(login_types, login_values):
            uinfo[login_type] = login_value

        # Hash and add password to uinfo
        password = hash_md5(password)
        uinfo['password'] = password
        
        # Invite link logic with groups
        invite_link_groups = None
        if data.get('identifier', None):
            invite_link_info= app.db.fetchone("""SELECT service_uuid, link_uuid FROM invite_link_temp 
            WHERE params->>'identifier' = %s""", [data.get('identifier')])

            if invite_link_info:
                service_info = app.db.fetchone("""SELECT uinfo->>'service_domain' AS service_domain, 
                initial_key AS initial_key FROM actor WHERE uuid=%s AND actor_type='service'""",
                                               [invite_link_info.get('service_uuid')])

                if service_info:
                    service_domain = service_info.get('service_domain')
                    request_data = dict(
                        service_uuid=app.config['SERVICE_UUID'],
                        link_uuid=invite_link_info.get('link_uuid')
                    )
                    request_data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'],
                                                          json_dumps(request_data, sort_keys=True))
                    response = requests.post(urljoin(service_domain, '/get_invite_link_info/'), json=request_data,
                                             headers=get_language_header())
                    if response.ok:
                        response_data = json.loads(response.content)
                        link = response_data.get('link')
                        admin_group = get_static_group('ADMIN')
                        if not isinstance(admin_group, dict) and admin_group.get('uuid') != link.get('group_uuid'):
                            invite_link_groups = [link.get('group_uuid')]

        if invite_link_groups:
            uinfo['groups'] += invite_link_groups

        # Save new classic_user in database
        query = "INSERT INTO actor(uinfo, actor_type) VALUES (%s::jsonb, %s) RETURNING *"
        values = [json_dumps(uinfo), 'classic_user']
        try:
            user = app.db.fetchone(query, values)
            if user:
                user['created'] = convert_datetime(user['created'])
        except Exception as e:
            logging_message(message='Exception on creating user! %s' % e)
            pwd = uinfo.pop('password')
            pwd_confirmation = uinfo.pop('password_confirmation')
            logging_message(message="Error with creating user "
                                    "core.auth_view.RegistrationView - registration_classic_user.\n "
                                    "uinfo - %s, password not exists - %s, "
                                    "password_confirmation not exists - %s" % (uinfo, not pwd, not pwd_confirmation))
            response = create_response_message(message=_("Some error occurred while creating actor. "
                                                         "Please try again."), error=True)
            return response, 400

        response = dict(
            user=user
        )
        return response, 200

    @staticmethod
    def collect_data_for_auth(data, salt_for: str = None):
        if data.get('actor_type', None) != 'classic_user':
            data['salt'] = get_user_salt({'qr_token': data.get('qr_token')}, salt_for=salt_for)

        data['service_uuid'] = app.config['SERVICE_UUID']

        uinfo = data.get('uinfo', {})
        uinfo['registered_on_service_uuid'] = app.config['SERVICE_UUID']
        uinfo['internal_user'] = app.config.get('INTERNAL_USERS_AFTER_REGISTRATION', False)
        data['uinfo'] = uinfo

        if app.config.get('AUTOADD_TO_SERVICE_LISTING_GROUP', True):
            data['add_to_listing_group'] = True

        data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'], json_dumps(data, sort_keys=True))
        return data
    
    @staticmethod
    def create_secure_uinfo(data, from_client_service, listing_group=None):
        """
        Getting email/names for actor from accepted_uinfo
        Adding auth default group.
        :param data: request data
        :return: uinfo.
        @subm_flow Create secure uinfo with auth default group and first_name/last_name
        """
        accepted_uinfo = data.get('uinfo', {})
        secure_uinfo = {}
        
        # Add first_name/last_name
        secure_uinfo['first_name'] = accepted_uinfo.get('first_name', '')
        secure_uinfo['last_name'] = accepted_uinfo.get('last_name', '')

        # Add default group only
        default_group = get_default_user_group()
        secure_uinfo['groups'] = [default_group.get('uuid')] if default_group else []

        # Check and add to listing group
        if data.pop('add_to_listing_group', False):
            if listing_group:
                secure_uinfo['groups'].append(listing_group)

        # Add email for actor with type 'user'
        if 'email' in accepted_uinfo and data.get('actor_type', '') != 'classic_user':
            secure_uinfo['email'] = accepted_uinfo['email']

        # Add service uuid where actor tried to register
        if from_client_service and 'registered_on_service_uuid' in accepted_uinfo:
            secure_uinfo['registered_on_service_uuid'] = accepted_uinfo['registered_on_service_uuid']
        elif not from_client_service:
            secure_uinfo['registered_on_service_uuid'] = app.config['SERVICE_UUID']

        # Add key whether user will be internal or not
        if from_client_service:
            secure_uinfo['internal_user'] = accepted_uinfo.get('internal_user', False)
        else:
            secure_uinfo['internal_user'] = app.config.get('INTERNAL_USERS_AFTER_REGISTRATION', False)

        return secure_uinfo

    @staticmethod
    def check_if_from_client_service(data):
        """
        Check if request was sent from client service.
        If request came from client service - verify signature
        :param data: request data
        :return: dict with flag from_service: True/False. If verification error also error True and error_message.
        @subm_flow
        """
        response = dict(
            from_service=False
        )
        if 'service_uuid' in data:
            query = "SELECT initial_key, uinfo ->> 'listing_group' as listing_group FROM actor WHERE uuid = %s AND actor_type = 'service'"
            values = [data.get('service_uuid')]
            service_info = app.db.fetchone(query, values)

            if not service_info:
                logging_message(message="Unknown service.\ndata - %s, service_info - %s" % (data, service_info))
                response = create_response_message(message=_("Unknown service."), error=True)
                response['from_service'] = True
                return response

            service_pub_key = service_info.get('initial_key')
            signature = data.pop('signature')
            if not verify_signature(service_pub_key, signature, json_dumps(data, sort_keys=True)):
                logging_message(message="Signature verification error.\n data - %s, signature - %s" % (data, signature))
                response = create_response_message(message=_("Signature verification failed."), error=True)
                response['from_service'] = True
                return response

            response['from_service'] = True
            response['client_service_uuid'] = data['service_uuid']
            response['client_service_listing_group'] = service_info['listing_group']

        return response


class APT54View(MethodView):
    """
    Authentication with getting apt54
    :group: (06) "02. Authentication process"
    @POST Authentication with getting apt54@
    @POST_body_request
    {
        "step": 1,
        "uuid": "d573cb16-ebc6-47d2-80a2-d5bd76493881"
    }
    @
    @POST_body_response
    {
        "salt": "7b1dfead35b494b882e84c60ec13c570"
    }
    @
    """
    @cross_origin()
    @data_parsing
    def post(self, **kwargs):
        data = kwargs.get("data")
        if data.get('step', None) and data.get('step', None) == 1 and data.get('uuid'):
            salt = create_new_salt({"uuid": data.get('uuid')}, salt_for='authentication')

            if not salt:
                logging_message(message="Error with creating salt. core.auth_view.APT54View - POST.\n "
                                        "salt - %s, uuid - %s" % (salt, data.get('uuid')))
                response = create_response_message(message=_("Some error occurred while creating verification data. "
                                                             "Please try again or contact the administrator."),
                                                   error=True)
                return make_response(jsonify(response), 400)

            response = dict(
                salt=salt
            )
            return make_response(jsonify(response), 200)

        response, status = self.authentication(data)

        if status == 200:
            salt = update_salt_data(data.get('uuid'), data.get('qr_token'))
            if not salt:
                logging_message(message='Error with salt updating')

        return make_response(jsonify(response), status)

    def authentication(self, data: dict):
        """
        Authentication step two. In this step check signed salt and if everything is good ask in auth apt54 and return
        it to user
        :param data: dictionary with uuid and signed salt
        :return: response, status: response - dictionary with apt54 of error=True flag with error message, status - http
        code
        Validate received data
        """
        signed_salt = data.get('signed_salt', None)
        uuid = data.get('uuid', None)
        qr_token = data.get('qr_token', None)
        step = data.get('step', None)

        if not uuid or not signed_salt or (not step == 2 and not qr_token):
            # There is no uuid or signed salt. Not full data set
            logging_message(message="Wrong data was sent. core.auth_view.APT54View - authentication.\n "
                                    "uuid - %s, signed_salt not exists - %s, "
                                    "step - %s, qr_token - %s" % (uuid, not signed_salt, step, qr_token))
            response = create_response_message(message=_("Invalid request data."), error=True)
            return response, 400

        if step:
            salt = get_user_salt({"uuid": uuid}, salt_for='authentication')
        else:
            salt = get_user_salt({'qr_token': qr_token, 'uuid': uuid}, salt_for='authentication')

        if not salt:
            # There is no salt generated for that public key
            logging_message(message="Wrong with getting salt. core.auth_view.APT54View - authentication.\n "
                                    "salt - %s, uuid - %s, qr_token - %s" % (salt, uuid, qr_token))
            response = create_response_message(message=_("There is no verification data based on received data. \n "
                                                         "Please get new QR code. "),
                                               error=True)
            return response, 400

        # Getting user public key and keys if they were regenerated
        initial_key, secondary_keys = get_public_key(uuid)
        if not initial_key and not secondary_keys:
            # User has no public key
            logging_message(message="User has no public key. core.auth_view.APT54View - authentication.\n "
                                    "uuid - %s, initial_key - %s, "
                                    "secondary_keys - %s" % (uuid, initial_key, secondary_keys))
            response = create_response_message(message=_("There is no your public key for your actor. "
                                                         "Please contact the administrator."), error=True)
            return response, 400

        # Verify salt signature with primary public key
        if verify_signature(initial_key, signed_salt, salt):
            # Signature verification passed with initial key
            # Getting apt54 from auth service
            return self.get_apt54_with_response(uuid)

        else:

            # Service use only primary key
            if app.config.get('PRIMARY_KEY_ONLY'):
                # Error response
                # Important service uses only primary initial key
                logging_message(message="Signature verification error Because PRIMARY_KEY_ONLY is True and "
                                        "verification by initial_key failed. "
                                        "core.auth_view.APT54View - authentication.\n ")
                response = create_response_message(message=_("Signature verification failed."), error=True)
                return response, 400

            if secondary_keys:
                for public_key in secondary_keys:
                    # Verify signature with secondary keys
                    # Check signature with secondary generated keys
                    if verify_signature(public_key, signed_salt, salt):
                        # Getting apt54 from auth service
                        return self.get_apt54_with_response(uuid)

        logging_message(message="Signature verification error. core.auth_view.APT54View - authentication.\n ")
        response = create_response_message(message=_("Signature verification failed."), error=True)
        return response, 400

    @staticmethod
    def get_apt54_with_response(uuid: str):
        if app.config.get('AUTH_STANDALONE'):
            apt54, status_code = get_apt54_locally(uuid)
        else:
            apt54, status_code = get_apt54(uuid)
        if status_code == 452:
            logging_message(message="Error with getting apt54. There is no such user with uuid - %s. "
                                    "core.auth_view.APT54View - get_apt54_with_response.\n" % uuid)
            response = create_response_message(message=_("There is no such actor. Please contact the administrator"),
                                               error=True)
            status = 400
        elif not apt54:
            logging_message(message="Error with getting apt54. core.auth_view.APT54View - get_apt54_with_response.\n "
                                    "uuid - %s" % uuid)
            response = create_response_message(message=_("Auth service is unreachable. "
                                                         "Please try again or contact the administrator."), error=True)
            status = 400
        elif status_code == 200:
            status = 200
            response = dict(
                apt54=json_dumps(apt54)
            )
        else:
            logging_message(message="Error with getting apt54. core.auth_view.APT54View - get_apt54_with_response.\n "
                                    "uuid - %s" % uuid)
            response = create_response_message(message=_("Some error occurred with getting your authentication token. "
                                                         "Please try again or contact the administrator."), error=True)
            status = 400
        return response, status


class ClientAuthenticationView(BaseAuth):
    """
    Authorization on client service
    @POST Authorization on client service@
    @POST_body_request
    {
        "step": "identification",
        "email": "qwerty@gmail.com",
        "actor_type": "classic_user"
    }
    @
    @POST_body_response
    {
        "temporary_session": "7qvJT9E9p8DzcOhBQ3xhhs9O5fuAafpX"
    }
    @
    """

    @cross_origin()
    @data_parsing
    def post(self, **kwargs):
        """
        POST /auth/ endpoint
        @subm_flow  POST /auth/ endpoint
        """
        self.data = kwargs.get('data')
        step = self.data.pop('step', None)
        if step not in ('identification', 'check_secret'):
            step = None
        self.qr_token = self.data.pop('qr_token', None)

        if step == 'identification' or self.qr_token:
            result = self.identificate_actor()
            if not result.get('error'):
                if not self.qr_token:
                    result = self.create_trust_element(
                        result.get('uuid'), result.get('actor_type')
                    )
                    status_code = 200
                else:
                    self.qr_user = result
            else:
                status_code = 400

        if step == 'check_secret' or hasattr(self, 'qr_user'):
            result = self.check_secret()
            if not result.get('error'):
                user_data = result['user_data']
                result = create_session(
                    result['user_data'],
                    auxiliary_token=self.qr_token,
                    depended_info=self.data.get("depended_services")
                )
                if not result.get('error'):
                    self.add_to_own_listing_group(user_data)
                    status_code = 200
                else:
                    status_code = 403
            else:
                status_code = 400

        if not step and not self.qr_token:
            result = create_response_message(_('Invalid request data.'), error=True)
            status_code = 400

        if hasattr(self, 'qr_user'):
            update_salt_data(self.qr_user['uuid'], self.qr_token)
            result['apt54'] = self.data.get('apt54') # FIXME: temporary solution
        return make_response(jsonify(result), status_code)


    def identificate_actor(self):
        query = """SELECT * FROM actor WHERE """
        appends_list = []
        values = {}
        actor_type = self.data.get('actor_type')
        if actor_type == "classic_user":
            login_types, login_values = self.parse_login_data(self.data)

            if not login_values or not all(login_values):
                logging_message(message="Wrong data was sent. "
                                        "Login types are %s, login values are %s" % (login_types, login_values))
                response = create_response_message(message=_("Invalid request data."), error=True)
                return response

            for login_type, login_value in zip(login_types, login_values):
                login_value_is_valid, invalid_msg = self.validate_login_value(login_type, login_value)
                if not login_value_is_valid:
                    response = create_response_message(message=invalid_msg, error=True)
                    return response

            for login_type, login_value in zip(login_types, login_values):
                query += "uinfo ->> {} = {} AND "
                appends_list += [sql.Literal(login_type), sql.Placeholder(login_type)]
                values[login_type] = login_value

            query += "actor_type = 'classic_user'"
        else:
            uuid = self.data.get('uuid')
            # FIXME: temporary solution
            if not uuid:
                if apt54_data := self.data.get('apt54'):
                    apt54 = apt54_data if isinstance(apt54_data, dict) else json.loads(apt54_data)
                    uuid = apt54['user_data'].get('uuid')
            if not uuid or not is_valid_uuid(uuid):
                logging_message(message="Wrong data was sent. UUID is %s" % (uuid))
                response = create_response_message(message=_("Invalid request data."), error=True)
                return response
            query += "{} = {}"
            appends_list += [sql.Identifier('uuid'), sql.Placeholder('uuid')]
            values['uuid'] = uuid

        query = sql.SQL(query).format(*appends_list)
        actor = app.db.fetchone(query, values)

        if not actor:
            actor = request_actor_from_auth_service(
                self.data if actor_type == "classic_user" else {'uuid': uuid}
            )
            if not actor:
                if actor_type  == "classic_user":
                    logging_message(message="Error with getting user."
                                            "\n %s - %s" % (login_types, login_values))
                    if login_types == ['email']:
                        msg = _("There is no actor with such email. Please check it.")
                    elif login_types == ['login']:
                        msg = _("There is no actor with such login. Please check it.")
                    elif login_types == ['phone_number']:
                        msg = _("There is no actor with such phone number. Please check it.")
                    elif login_types == ['email', 'login']:
                        msg = _("There is no actor with such email and login. Please check it.")
                    else:
                        msg = _("There is no actor with such data. Please check it.")
                else:
                    logging_message(message="Error with getting actor."
                                            "\n UUID - %s" % (uuid))
                    msg = _("There is no actor with such uuid.")
                response = create_response_message(message=msg, error=True)
                return response

        return actor


    def create_trust_element(self, actor_uuid, actor_type):
        if actor_type == 'classic_user':
            return {
                'temporary_session': create_temporary_session(actor_uuid)
            }
        else:
            salt = create_new_salt({"uuid": actor_uuid}, salt_for='authentication')
            if not salt:
                logging_message(message="Error with creating salt.\n"
                                        "salt - %s, actor_uuid - %s" % (salt, actor_uuid))
                response = create_response_message(message=_("There is no verification data based on received data."),
                                                  error=True)
            else:
                response = {
                    'salt': salt
                }
                if actor_type != 'service':
                    if depended_services_salts := get_salt_from_depended_services(self.data):
                        response.update({
                            "depended_services": depended_services_salts,
                        })
            return response


    def check_secret(self):
        if self.data.get('actor_type') == "classic_user":
            temporary_session = self.data.get('temporary_session')
            if temporary_session:
                user_data = app.db.fetchone(
                    "SELECT * FROM actor WHERE actor_type='classic_user' AND uuid = (SELECT actor_uuid FROM temporary_session WHERE temporary_session=%s)",
                    (temporary_session,)
                )
                delete_temporary_session(temporary_session)
                if user_data:
                    hashed_password = user_data['uinfo'].get('password')
                    if hash_md5(hashed_password + temporary_session) == self.data.get('password'):
                        return {'user_data': user_data}
            return create_response_message(message=_("Password verification failed."), error=True)

        else:
            signed_salt = self.data.get('signed_salt')
            if self.qr_token:
                user = self.qr_user
            else:
                user = app.db.fetchone(
                    "SELECT * FROM actor WHERE uuid = %s", 
                    (self.data.get('uuid'),)
                )
                if not user:
                    response = create_response_message(message=_("There is no actor with such uuid."), error=True)
                    return response
            uuid = user['uuid']

            salt = get_user_salt({'qr_token': self.qr_token, 'uuid': uuid}, salt_for='authentication')
            if not salt:
                # There is no salt generated for that public key
                logging_message(message="Error with getting salt during authentication process.\n "
                                        "UUID - %s, qr_token - %s" % (uuid, self.qr_token))
                response = create_response_message(message=_("There is no verification data based on received data."), error=True)
                return response

            # Getting user public key and keys if they were regenerated
            initial_key, secondary_keys = get_public_key(uuid)

            # Actor has public keys
            if not initial_key and not secondary_keys:
                logging_message(message="Error with getting initial_key. initial_key - %s" % initial_key)
                response = create_response_message(message=_("There is no your public key for your actor. "
                                                            "Please contact the administrator.\n"), error=True)
                return response

            # Verify signed salt with primary public key
            signature_verified = False
            if verify_signature(initial_key, signed_salt, salt):
                signature_verified = True
            else:
                if app.config.get('PRIMARY_KEY_ONLY') and secondary_keys:
                    # Important service uses only primary initial key
                    logging_message(message="Signature verification error because PRIMARY_KEY_ONLY is True and "
                                            "verification by initial_key failed.\n")
                elif secondary_keys:
                    for public_key in secondary_keys:
                        # Check signature with secondary generated keys
                        # Verify salt signature with secondary keys
                        if verify_signature(public_key, signed_salt, salt):
                            signature_verified = True
                            break

            if signature_verified:
                return {'user_data': user}
            else:
                return create_response_message(message=_("Signature verification failed."), error=True)


class RootAPT54View(MethodView):
    """
    @POST Identificate actor and create session with Root self signed APT54@
    @POST_body_request
    {
        "apt54": {
            "signature": "30450220121503996c58fd118fd065fc4c638ba235f00ddee8446c514f3d1ff965408e8f022100898ffeb489f001ca4b4fe216c0e6d9ac321a271dd75a65d6aa8d3496cb89cc53",
            "expiration": "2023-07-20 14:56:11"
            "user_data": {
                "uuid": "66356f2e-987a-4031-af59-30a408f2fff5",
                "uinfo": {
                    "login": "root",
                    "groups": ["4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"],
                    "password": "d8578edf8458ce06fbc5bb76a58c5ca4",
                    "last_name": "root",
                    "first_name": "root"
                    },
                "created": "2023-03-24 09:09:59",
                "actor_type": "classic_user",
                "initial_key": "04a35e8a437a54d4826e83c3c476201a5259a3933a07cc3c6e056b58de8f90802293c4b343a2e4ce789c951c9cb5ddf1cb59fdef76d8d96e0f5f2b1a8e617e6bf2",
                "secondary_keys": null,
                "root_perms_signature": "30460221008241fd549d86047c709a18b43b6f1c1b67ba4c1192f2d6dce735cceb0af13d3a0221008483e430be2e81b1211d14b81c28ba1bf7974dd55cb707cc26a5bb0e5503cafd"
            },
        },
        "create_session": true
    }
    @
    @POST_body_response
    {
        "message": "Successfully executed",
        "session_token": "7qvJT9E9p8DzcOhBQ3xhhs9O5fuAafpX",
        "expiration": "2023-08-01 14:56:20"
    }
    @
    """

    @cross_origin()
    @data_parsing
    def post(self, data):
        apt54 = data.get('apt54')
        status_code = None
        if apt54 and isinstance(apt54, dict):
            apt54_signature = apt54.get('signature')
            user_data = apt54.get('user_data', {})
            root_perms_signature = user_data.get('root_perms_signature')
            initial_key = user_data.get('initial_key')
            uuid = user_data.get('uuid')
            # Check apt54 values
            if all((apt54_signature, root_perms_signature, initial_key, uuid)):
                service_public_key = app.config['AUTH_PUB_KEY'] if not app.config.get('AUTH_STANDALONE') else app.config['SERVICE_PUBLIC_KEY']
                # Check actor is root
                if verify_signature(service_public_key, root_perms_signature, uuid + initial_key):
                    user_data = json_dumps(user_data, sort_keys=True)
                    expiration = apt54.get('expiration')
                    verifying_data = str(user_data) + str(expiration)
                    # Verify apt54 signature
                    if verify_signature(initial_key, apt54_signature, verifying_data):
                        # Check apt54 expiration
                        if not apt54_expired(expiration):
                            query = """SELECT * FROM actor WHERE uuid = %s"""
                            values = [uuid]
                            actor = app.db.fetchone(query, values)
                            if not actor:
                                actor = create_actor(apt54)
                            if actor:
                                result = create_response_message(_('Successfully executed'))
                                status_code = 200
                                if data.get('create_session'):
                                    session_data = create_session(actor)
                                    result.update(session_data)
                            else:
                                result = create_response_message(_('Error with getting actor'), error=True), 
                        else:
                            result = create_response_message(_('APT54 expired.'), error=True), 
                    else:
                        result = create_response_message(_('Signature verification failed.'), error=True), 
                else:
                    result, status_code = create_response_message(_('Actor must be Root'), error=True), 403
            else:
                result = create_response_message(_('Invalid APT54 was sent.'), error=True), 
        else:
            result = create_response_message(_('Invalid request data.'), error=True), 
        return make_response(jsonify(result), status_code if status_code else 400)


class SaveSession(MethodView):
    """
    @POST Save session in cookies with flask session module based on request body@
    @POST_body_request
    {
        "session_token": "2dfTUcgbyj2GGIUc2RuanS8jkxGO6Qni"
    }
    @
    @POST_body_response
    {
        "message": "Session token successfully saved."
    }
    @
    """
    def post(self):
        """
        Save session in cookies with flask session module.
        @subm_flow Save session in cookies with flask session module.
        """
        if (not request.is_json
            or not request.json.get('session_token') 
            or not isinstance(request.json.get('session_token'), str)):
            response = create_response_message(message=_("Invalid request type."), error=True)
            return make_response(jsonify(response), 422)

        session_token = request.json.get('session_token')

        if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM service_session_token WHERE session_token = %s)""",
                           [session_token]).get('exists'):
            session['session_token'] = session_token
            message = _("Session token successfully saved.")
        else:
            message = _(f"Unknow session token - {session_token}")
            logging_message(message=message, level='warning')

        response = dict(
            message=message
        )
        return make_response(jsonify(response), 200)


class GetSession(MethodView):
    """
    @POST Get session based on request body@
    @POST_body_request
    {
        "qr_token": "Wfkjwenk4ksjg6oo6",
        "temporary_session": "7h4s5kjI5CFU8KLD74TMc1QSVHWP8Sk0"
    }
    @
    @POST_body_response
    {
        "session_token": "XVKKdV86W8uHmdnAfQ1nWSxqbfECHpiQ"
    }
    @
    """
    def post(self):
        """
        Get session by qr code and temporary session.
        :return: session token
        @subm_flow
        """

        if not request.is_json:
            response = create_response_message(
                message=_("Invalid request type."), error=True)
            return make_response(jsonify(response), 422)

        if request.json.get("qr_token"):
            session_token = get_session_token_by_auxiliary(request.json.get('qr_token'))
            if not session_token:
                session_token = dict(
                    message=_("There is no session token.")
                )
            response = session_token

        temporary_session = request.json.get('temporary_session')

        if temporary_session:
            if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM temporary_session WHERE temporary_session = %s)""",
                               [temporary_session]).get('exists'):
                session_token = get_session_token_by_auxiliary(
                    temporary_session)
                if session_token:
                    app.db.execute("""UPDATE service_session_token SET auxiliary_token = NULL WHERE auxiliary_token = %s""",
                                   [temporary_session])

                delete_temporary_session(temporary_session)
                response = session_token

        return make_response(jsonify(response), 200)


class AuthorizationView(MethodView):
    """
    @GET Submodule Biom mode. Get login template. Automatically adding js, css scripts from static folder according to app config.@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 125087
    Access-Control-Allow-Origin: *
    Vary: Cookie
    @
    """
    @cross_origin()
    def get(self, **kwargs):
        """
        Get login template.
        Automatically adding js, css scripts from static folder according to app config.
        :param kwargs: dict. OPTIONAL. Example:
        {
            "registration_url": https://example.com/registration or /registration/ or url_for('registration'),
            "authentication_url": https://example.com/authentication or /authentication/ or url_for('authentication'),
            "redirect_url_after_authentication": /some_url/ or /,
            "save_session_url": https://example.com/save or /save/ or url_for('save'),
            "get_qr_url": https://example.com/qr or /qr/ or url_for('qr'),
            "qr_login_url": https://example.com/qr_login or /qr_login/ or url_for('qr_login'),
            "sso_generation_url": https://example.com/sso or /sso/ or url_for('sso'),
            "sso_login_url": https://example.com/sso_login or /sso_login/ or url_for('sso_login'),
        }
        :return: template
        @subm_flow
        """
        self.service_domain = app.config.get("SERVICE_DOMAIN")
        self.is_standalone = app.config.get('AUTH_STANDALONE', False)
        self.is_auth_service = check_if_auth_service()
        self.sso_mode = app.config.get('SSO_MODE', True)

        # default context
        context = {
            'standalone': self.is_standalone,
            'is_auth_service': self.is_auth_service,
            'sso_mode': self.sso_mode,
            'current_language': self.define_language(),
            'language_information': app.config.get('LANGUAGES_INFORMATION', []),
            'service_name': app.config.get('SERVICE_NAME', 'service').capitalize()
        }

        # static files with service domain
        context.update(self.get_static_files_urls())

        # getting all urls with services domains
        context.update(self.get_urls(**kwargs))

        if not self.is_standalone:
            context.update(self.get_qr_token_content())
            context['depended_services'] = self.get_depended_services()

        return render_template('auth.html', **context)


    def define_language(self):
        language_information = app.config.get('LANGUAGES_INFORMATION', LANGUAGES_INFORMATION)
        current_language = None
        for language in language_information:
            if language.get('code') == get_service_locale():
                current_language = language

        if not current_language:
            current_language = {"code": "en", "name": "English"}
        return current_language


    def get_static_files_urls(self):
        get_link = lambda name: urljoin(self.service_domain, url_for('auth_submodule.static', filename=name))

        styles = [
            get_link('css/auth.css'),
            get_link('css/materialdesignicons.min.css'),
        ]
        scripts = [
            get_link('js/x-notify.js'),
            get_link('js/md5.min.js'),
            get_link('js/default_authorization.js'),
        ]
        if not self.is_standalone:
            scripts += [
                get_link('js/qrLib.js'),
                get_link('js/qr_code_authorization.js'),
            ]
            if not self.is_auth_service and self.sso_mode:
                scripts += [get_link('js/sso_authorization.js')]

        return {'styles': styles, 'scripts': scripts}


    def get_urls(self, **kwargs):
        make_url = lambda endpoint: urljoin(self.service_domain, endpoint)

        urls = {
            'authentication_url': make_url(kwargs.get('authentication_url', url_for('auth_submodule.auth'))),
            'registration_url': make_url(kwargs.get('registration_url', url_for('auth_submodule.reg'))),
            'redirect_url_after_authentication': kwargs.get(
                'redirect_url_after_authentication', app.config.get('REDIRECT_URL_AFTER_AUTHENTICATION', '/')),
        }
        if not self.is_standalone:
            urls['get_qr_url'] = make_url(kwargs.get('get_qr_url', url_for('auth_submodule.qr-code')))
            urls['qr_login_url'] = make_url(kwargs.get('qr_login_url', url_for('auth_submodule.auth_qr_login')))
            urls['save_session_url'] = make_url(kwargs.get('save_session_url', url_for('auth_submodule.save_session')))
            if not self.is_auth_service and self.sso_mode:
                urls['sso_generation_url'] = make_url(kwargs.get('sso_generation_url', url_for('auth_submodule.auth-sso')))
                urls['sso_login_url'] = make_url(kwargs.get('sso_login_url', url_for('auth_submodule.auth_sso_login')))
        return urls


    def get_depended_services(self):
        depended_services = []
        make_url = lambda domain, endpoint: urljoin(domain, url_for(f'auth_submodule.{endpoint}'))

        depended_services_source = get_depended_services_source()
        for name, domain in depended_services_source.items():
            service_data = {
                'name': name.capitalize(),
                'authentication_url': make_url(domain, 'auth'),
                'save_session_url': make_url(domain, 'save_session')
            }
            if not self.is_auth_service and self.sso_mode:
                service_data['sso_generation_url'] = make_url(domain, 'auth-sso')
            depended_services.append(service_data)
        return depended_services


    def get_qr_token_content(self):
        # get full content from GetQRCodeView
        auth_response = GetQRCodeView().get(data=dict(qr_type='authentication'))
        authentication_content = auth_response.json

        reg_response = GetQRCodeView().get(data=dict(qr_type='registration'))
        registration_content = reg_response.json
        registration_content['depended_services'] = authentication_content.get('depended_services')

        # get token only data with depended services if exists
        authentication_qr_token = {
            'qr_token': authentication_content.get('qr_token'),
            'qr_type': 'authentication',
        }
        registration_qr_token = {
            'qr_token': registration_content.get('qr_token'),
            'qr_type': 'registration'
        }
        if authentication_content.get('depended_services'):
            authentication_qr_token['depended_services'] = {}
            registration_qr_token['depended_services'] = {}
            for name, data in authentication_content.get('depended_services').items():
                authentication_qr_token['depended_services'][name] = {
                    'qr_token': data.get('qr_token'),
                    'qr_type': 'authentication'
                }
                registration_qr_token['depended_services'][name] = {
                    'qr_token': data.get("qr_token"),
                    "qr_type": 'registration'
                }

        return {
            'authentication_content': authentication_content,
            'authentication_qr_token': authentication_qr_token,
            'registration_content': registration_content,
            'registration_qr_token': registration_qr_token
        }


class GetQRCodeView(MethodView):
    """
    QR code generation
    Parameters: - qr_token - salt - domain - biom_uuid"
    @GET QR code generation@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    {
        "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAhIAAAISAQAAAACxRhsSAAAEzklEQVR4nO2dX2rrOhDGv7kO5FGGLKBLUXZw19QldQf2UrKAgvVYUJj7oBlJbs9pD5xE5IZPD8VxlB82fIzmn1RR/O1Y//lrBEAGGWSQQQYZZJBBBhmNITYOkDOu5QrAVeScRIB0gP0BIOfk8883fg4yyPjNUFVVRFVV3abuj30fMhA1o0xZQoZNqT9bHuVdyHh+RnLruM4A0OR4OSrWeVJ9bQYUgJvcWz8HGWT8ESNuAJBE7HP4EMSLSzRuQLm693OQQcZPDJGXDCB8SDObumDS5qQOeQ4yyLDhsgsKIAFlyQeuEIRNJS6AAFMWhHdp8/rywKO8CxlPz1hFRGQG5JwOkHM6KuKlj/IRL8diT8VSAtU1eLB3IeMJGSXebwPApOakYioRfbkqk7cvv2C8T8b9GZaXKumnbVJdgqWfXKwAik79C+alyBjOqPnTjCLWIscmTEz+ESgSLXquYqVOybg/w1bxBb6oL+X2pKqa+yrAEnIJ+lU1249pT8kYw3AlboAt+UApQBWLuezn9Sa3avxR3oWM52XsdFqt6IK6xrs9BYL5B2ZPQ6Y9JWMUw+1kuWrBVJUjJu0dgqC6m0KdkjGC4VoL5nLaul/7UFrQHzV/dQ2oUzKGMtLR86fBSqaWA4BpV1/nXrv6KkeV882fgwwyfjWs2hT1WhtPAF3nTWUVQJGmDGDKQBIgXg4e64d30ds9BxlkfDtaXsrbTN01jc0/LeE/zCGo2QDGUWQMYtQ4ysKlsqiXsdUUv2ejuquaCKBOybg/o9pTL0CVvFTINcDPuypUzVCZoaVOyRjB6Oyp3WhirXNq/rSY3HqPOiVjEKOu8TA5Vg+0T/Gj9knD59GekjGcIeegXbO+LukAfRXfahpVVc6th6rtPL3xc5BBxh8wQrZ9fOtLhmk35NJFrXo5lC+8CfDKPmkyRjFqfb8t6i27v1vo4zZ1bgDjfTJGMrpteQoAnt0/ZSBsQHw7ZUGaAeAqus7vB5S0P64H5vnJGMTo7GnrNOn6+aMnUW2e9tkAxlFkDGLs8vy7gr7l9DHtGqS2vk+VOiVjEOOzf9ra9u2em1dtXadlBOZPyRjG+NzP7zET4DVS+9OaUD3AYn2fjGGMrv/U3NC2P6/eW6piY+1IYT8/GQMZfZ9065daWo20Oqnwxb+r/lOnZIxhdDtKu5t157MF/U3AdbVvgzol4+6MXR+KHzbhIVTuu1Nt/OLbR3kXMp6X0Z3C0wVTVYS+dd/7pRagGlX6p2QMY1g9aj0DQMgH217ydnQ3IJ2yAGLVqridMoCrAGkG61FkDGL05/ZYK389QWr7Wt9vg/aUjIGML+f11ZOmPAfgDkEtRXnbNP1TMoYxyrrvHXpTVqSTYv13UgGOKqUjBVOWuCjE+k/LPTevj/IuZDwvw/dFLwCQTuWTAIesxQ2tB1AgzbB+qZBhfuxyq+cgg4xvRwv1PSXlV81i2hY+1vfJeCDGpPr6koGoH1Jku758lB0ouqSjlVaXxHPPyRjG+GxPW7wP1NJ+rKXVuiWa50uRMZLx+f/xlXu1+2R3VF/um6vqDlXqlIz7MzzPX9bwCYhvMxAVAJIl+yVup+yL/HX3n3xu9hxkkPHdEP15zg9jfZR3IYMMMsgggwwyyCDj/8/4D0ve+3npfjH4AAAAAElFTkSuQmCC"
    }
    @
    """

    @cross_origin()
    def get(self, **kwargs):
        if request.args.get('qr_type', None) == 'application':
            img_io = self.generate_qr_image(ERP_APP_URL)
            response = dict(
                qr_code=base64.b64encode(img_io.getvalue()).decode(),
            )
            return make_response(jsonify(response), 200)

        query = """SELECT uinfo->>'service_domain' AS service_domain FROM actor WHERE uuid = %s"""
        service_domain = app.db.fetchone(query, [app.config.get('SERVICE_UUID')])
        if not service_domain:
            raise ActorNotFound

        data = kwargs.get('data', {})

        registration_url = data.get('registration_url') if data.get('registration_url') else \
            urljoin(service_domain.get('service_domain'), url_for('auth_submodule.reg'))
        apt54_url = urljoin(service_domain.get('service_domain'), url_for('auth_submodule.apt54'))
        authentication_url = data.get('authentication_url') if data.get('authentication_url') else \
            urljoin(service_domain.get('service_domain'), url_for('auth_submodule.auth'))
        about_url = data.get('about_url') if data.get('about_url') else \
            urljoin(service_domain.get('service_domain'), url_for('auth_submodule.about'))

        qr_type = None

        if request.args.get('qr_type'):
            if request.args.get('qr_type') not in ['registration', 'authentication']:
                logging_message(message="Error with getting qr_type from request args. core.auth_view.QRCodeView - "
                                        "GET.\n request.args - %s" % request.args)
                response = create_response_message(message=_("Unknown QR type. "
                                                             "Please try again or contact the administrator."),
                                                   error=True)
                return make_response(jsonify(response), 400)

            qr_type = request.args.get('qr_type')

        if data.get('qr_type') and not qr_type:
            if data.get('qr_type') not in ['registration', 'authentication']:
                logging_message(message="Error with getting qr_type from kwargs. core.auth_view.QRCodeView - "
                                        "GET.\n kwargs - %s" % kwargs)
                response = create_response_message(message=_("Unknown QR type. "
                                                             "Please try again or contact the administrator."),
                                                   error=True)
                return make_response(jsonify(response), 400)

            qr_type = data.get('qr_type')

        if not qr_type:
            logging_message(message="Error with getting qr_type from request args and kwargs. "
                                    "core.auth_view.QRCodeView - GET.\n")
            response = create_response_message(message=_("There is no QR type. "
                                                         "Please try again or contact the administrator."), error=True)
            return make_response(jsonify(response), 400)

        qr_token = generate_qr_token()
        salt = create_new_salt(user_info={'qr_token': qr_token}, salt_for=qr_type)
        if not salt:
            logging_message(message="Error with creating salt. core.auth_view.QRCodeView - GET.\n salt - %s" % salt)
            response = create_response_message(message=_("Some error occurred while creating verification data. "
                                                         "Please try again or contact the administrator."),
                                               error=True)
            return make_response(jsonify(response), 400)

        if qr_type == 'registration':
            data = dict(
                qr_token=qr_token,
                salt=salt,
                about_url=about_url,
                registration_url=registration_url,
                apt54_url=apt54_url, # TODO: remove it later
                authentication_url=authentication_url,
                auth_domain=get_auth_domain(),
            )
            response = data
        else:
            response = dict(
                qr_token=qr_token,
                salt=salt,
                about_url=about_url,
                apt54_url=apt54_url, # TODO: remove it later
                authentication_url=authentication_url,
                auth_domain=get_auth_domain(),
            )
            response.update(
                {"depended_services": self.get_depended_qr_info()}
            )
        return make_response(jsonify(response), 200)

    def get_depended_qr_info(self):
        services_info = dict()
        depended_services_source = get_depended_services_source()
        for name, domain in depended_services_source.items():
            try:
                services_info.update({
                    name: dict(
                        requests.get(
                            urljoin(domain, "/get_qr_code/"),
                            params={"qr_type": "authentication"}
                        ).json()
                    )}
                )
            except Exception:
                continue
        return services_info

    @staticmethod
    def generate_qr_image(data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image()
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io


class AuthQRCodeAuthorizationView(MethodView):
    """
    @POST Login with QR code@
    @POST_body_request
    Content-Type: application/x-www-form-urlencoded
    {"qr_token": "bAX4em9XaG5fivZMdj0CSD0MV2XgYLOV", "qr_type": "authentication"}:
    @
    @POST_body_response
    {
        "session_token": "Ju4GMkL3vrjEAXVpAK38f3QBImlD8zQY"
    }
    @
    """

    @cross_origin()
    def post(self):
        if not request.is_json:
            response = create_response_message(
                message=_("Invalid request type."), error=True)
            return make_response(jsonify(response), 422)

        data = request.json
        if data.get('qr_token'):
            session_token = get_session_token_by_auxiliary(data.get('qr_token'))
            if not session_token:
                response = dict(
                    message=_("There is no session token.")
                )
                return jsonify(response), 200

            for name, service_data in data.get("depended_services", {}).items():
                depended_services_source = get_depended_services_source()
                try:
                    url = urljoin(depended_services_source.get(name.lower()), "/get_session/" )
                    response_json = requests.post(url, json=service_data).json()
                except:
                    response_json = None
                if response_json:
                    session_token[name + "_session_token"] = response_json.get("session_token")
            response = dict(session_token)
            return jsonify(response), 200
        else:
            return jsonify('QR token not found'), 400


class AuthSSOGenerationView(MethodView):
    """
    @GET Allow to authenticate with Auth session@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    {
        "domain": "http://192.168.1.105:5000/auth_sso/",
        "service": "auth",
        "session": "Ng2YI6dovdBU5dgnFzfdlyvhN8e3Wh1m",
        "uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
    }
    @
    @POST Session generation on service based on request body@
    @POST_body_request
    {
        "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "apt54": {
        "signature": "30450220121503996c58fd118fd065fc4c638ba235f00ddee8446c514f3d1ff965408e8f022100898ffeb489f001ca4b4fe216c0e6d9ac321a271dd75a65d6aa8d3496cb89cc53",
        "user_data": {
            "root": true,
            "uuid": "66356f2e-987a-4031-af59-30a408f2fff5",
            "uinfo": {
                "email": "qwerty@gmail.com",
                "groups": ["4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"],
                "password": "d8578edf8458ce06fbc5bb76a58c5ca4",
                "last_name": "qwerty_pu",
                "first_name": "qwerty_put"
                },
            "created": "2022-04-21 09:09:59",
            "actor_type": "classic_user",
            "initial_key": "04a35e8a437a54d4826e83c3c476201a5259a3933a07cc3c6e056b58de8f90802293c4b343a2e4ce789c951c9cb5ddf1cb59fdef76d8d96e0f5f2b1a8e617e6bf2",
            "secondary_keys": null,
            "root_perms_signature": "30460221008241fd549d86047c709a18b43b6f1c1b67ba4c1192f2d6dce735cceb0af13d3a0221008483e430be2e81b1211d14b81c28ba1bf7974dd55cb707cc26a5bb0e5503cafd"
            },
        "expiration": "2022-05-06 14:56:11"
            },
        "temporary_session": "f2K71OqINJkdYWDxOmDP7AEG12qtxv8e",
        "signature": "304602210087beb04a22e8dc294fcd618df319e5a9a2932fd0d0e1b997ba3981d4fb15aa360221008803d47fc5e622f933397637e4dc7aaa847ae616311ee456413b7793b264c33b"
    }
    @
    @POST_body_response
    {
        "message": "Session token was successfully created."
    }
    @
    """
    
    @cross_origin()
    def get(self):
        temporary_session = create_temporary_session()
        domain = urljoin(get_auth_domain(), '/auth_sso/')
        data = dict(
            domain=domain,
            session=temporary_session,
            uuid=app.config['SERVICE_UUID'],
            service=app.config.get("SERVICE_NAME", "").lower()
        )
        return make_response(jsonify(data), 200)

    @service_only
    @cross_origin()
    def post(self):
        data = request.json
        signature = data.pop('signature', None)
        if not data or not signature:
            logging_message(message="Error with data. core.auth_view.AuthSSOView - POST.\n "
                                    "data - %s, signature - %s" % (data, signature))
            response = create_response_message(message=_("Invalid request data."), error=True)
            return make_response(jsonify(response), 422)

        if not verify_signature(app.config['AUTH_PUB_KEY'], signature, json_dumps(data, sort_keys=True)):
            logging_message(message="Signature verification. core.auth_view.AuthSSOView - POST.\n "
                                    "data - %s, signature - %s" % (data, signature))
            response = create_response_message(message=_("Signature verification failed."), error=True)
            return make_response(jsonify(response), 400)

        apt54 = data.get('apt54')
        if not apt54:
            logging_message(message="There is no APT54 token. core.auth_view.AuthSSOView - POST.\n data - %s" % data)
            response = create_response_message(message=_("There is no authentication token. "
                                                         "Please try again or contact the administrator."), error=True)
            return make_response(jsonify(response), 400)

        uuid = apt54['user_data'].get('uuid', None)
        if not uuid:
            logging_message(message="There is not uuid in APT54. core.auth_view.AuthSSOView - POST\n "
                                    "apt54 - %s" % apt54)
            response = create_response_message(message=_("Invalid data in your authentication token. "
                                                         "Please try again or contact the administrator."), error=True)
            return make_response(jsonify(response), 400)

        if not actor_exists(uuid):
            # Add actor info in user_data key, cause create_actor function, creates user by apt54.
            actor = dict(
                user_data=data.get('actor')
            )
            if not create_actor(actor):
                # Error while creating user
                logging_message(message="Error with creating actor. core.auth_view.AuthSSOView - POST.\n "
                                        "actor - %s" % actor)
                response = create_response_message(message=_("Some error occurred while creating actor. "
                                                             "Please try again or contact the administrator."),
                                                   error=True)
                return make_response(jsonify(response), 400)

        response = create_session_with_apt54(apt54, auxiliary_token=data.get('temporary_session'))
        if isinstance(response, dict) and response.get('error'):
            return make_response(jsonify(response), 401)

        session_token = response
        if not session_token:
            logging_message(message="Error with creating session token. core.auth_view.AuthSSOView - POST.\n "
                                    "error - %s" % response)
            response = create_response_message(message=_("Some error occurred while creating session token. "
                                                         "Please try again or contact the administrator."), error=True)
            return make_response(jsonify(response), 400)

        response = create_response_message(message=_("Session token was successfully created."))
        return make_response(jsonify(response), 200)


class AuthSSOAuthorizationView(MethodView):
    """
    @POST Get session token after back redirect from auth single sign on@
    @POST_body_request
    Content-Type: application/x-www-form-urlencoded
    {"temporary_session": "f2K71OqINJkdYWDxOmDP7AEG12qtxv8e"}:
    @
    @POST_body_response
    {
        "session_token": {
            "session_token": "VUHEI6Tdul9YCQ3fzHZEmhpByB3CZnMj"
        }
    }
    @
    """
    @cross_origin()
    def post(self):
        """
        Get session token after back redirect from auth single sign on.
        :param data: dict with salt from auth and signature.
        :return: message on response
        """
        if not request.is_json:
            response = create_response_message(
                message=_("Invalid request type."), error=True)
            return make_response(jsonify(response), 422)

        data = request.json
        temporary_sessions = {key: value for key,
                                             value in data.items() if "temporary" in key}
        if temporary_sessions:
            if temporary_sessions.get('temporary_session'):
                temporary_session = temporary_sessions.pop('temporary_session')
                if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM temporary_session WHERE temporary_session = %s)""",
                                   [temporary_session]).get('exists'):
                    session_token = get_session_token_by_auxiliary(
                        temporary_session)
                    if session_token:
                        apt54 = app.db.fetchone(
                            """UPDATE service_session_token SET auxiliary_token = NULL WHERE auxiliary_token = %s RETURNING apt54""",
                            [temporary_session])
                        session_token = dict(session_token)

                        delete_temporary_session(temporary_session)

                        BaseAuth.add_to_own_listing_group(apt54['apt54']['user_data'])
                    else:
                        session_token = dict()

                    for name, temporary_session in temporary_sessions.items():
                        service_name = name.replace("temporary_session_", "")
                        depended_services_source = get_depended_services_source()
                        response_json = requests.post(
                            depended_services_source.get(service_name) + "/get_session/",
                            json={"temporary_session": temporary_session}
                        ).json()
                        if response_json:
                            session_token[service_name + "_session_token"] = response_json.get("session_token")
                    response = {'session_token': session_token }
                    return jsonify(response), 200
        return jsonify('Temporary session does not exists'), 400


class CreateSessionTokenByUuidView(MethodView):
    """
    @POST Create session token by actor uuid. Admin only
    @POST_body_request
    {
        "actor_uuid": "8e482f30-de28-4a5a-8e5e-4c525c72763d"
    }
    @
    @POST_body_response
    {
        "session_token": "2dfTUcgbyj2GGIUc2RuanS8jkxGO6Qni"
    }
    @
    """
    @admin_only
    @cross_origin()
    @data_parsing
    def post(self, data):
        try:
            session_token = create_masquerading_session_token(data.get('actor_uuid'), token_type='created_by_admin')
        except ValueError as e:
            response, status_code = create_response_message(message=e.args[0], error=True), 400
        except ActorNotFound:
            response, status_code = create_response_message(message="Actor not found", error=True), 404
        else:
            response, status_code = {'session_token': session_token}, 200
        return make_response(jsonify(response), status_code)


class AboutView(MethodView):
    """
    @GET Submodule Biom mode. Get page with json information about service and biom@
    @GET_body_request
    Content-Type: None
    @
    @GET_body_response
    {
        "auth_biom_public_key": "04cdd9c94a9ecbc7fd4a0c2582a6e8b514edbc26d6281fabbc02cdbd01235772e81e6c179c8ceecfb39046972607a714267ca6cabafd69c2c21e41f76745e1364e",
        "biom_domain": "http://192.168.1.105:5000",
        "biom_name": null,
        "biom_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
        "service_domain": "http://192.168.1.105:5002",
        "service_name": "Entity",
        "service_uuid": "db8972cd-c9e9-4cb9-9338-822209b71926"
    }
    @
    """
    @cross_origin()
    def get(self):
        query = """SELECT uuid AS uuid, uinfo->>'service_name' AS service_name, 
        uinfo->>'service_domain' AS service_domain FROM actor WHERE uuid = %s AND actor_type = 'service'"""
        service_info = app.db.fetchone(query, [app.config['SERVICE_UUID']])

        if not service_info:
            logging_message(message="There is not service info. core.auth_view.AboutView - GET.")
            response = create_response_message(message=_("Some error occurred while getting service info."), error=True)
            return make_response(jsonify(response), 400)

        query = """SELECT uuid AS uuid, initial_key AS biom_public_key, uuid,
        uinfo->>'biom_name' AS biom_name,
        uinfo->>'service_domain' AS service_domain 
        FROM actor WHERE actor_type='service' AND initial_key=%s"""
        if app.config.get('AUTH_STANDALONE'):
            auth_info = app.db.fetchone(query, [app.config.get('SERVICE_PUBLIC_KEY')])
        else:
            auth_info = app.db.fetchone(query, [app.config.get('AUTH_PUB_KEY')])
        if not auth_info:
            logging_message(message="There is not biom info. core.auth_view.AboutView - GET.")
            response = create_response_message(message=_("Some error occurred while getting service info."), error=True)
            return make_response(jsonify(response), 400)

        response = dict(
            biom_uuid=auth_info.get('uuid'),
            biom_name=auth_info.get('biom_name', 'Unknown'),
            auth_biom_public_key=auth_info.get("biom_public_key"),
            biom_domain=auth_info.get('service_domain', 'Unknown'),
            service_uuid=service_info.get('uuid', 'Unknown'),
            service_name=service_info.get('service_name', 'Unknown'),
            service_domain=service_info.get('service_domain', 'Unknown'),
        )

        return make_response(jsonify(response), 200)
