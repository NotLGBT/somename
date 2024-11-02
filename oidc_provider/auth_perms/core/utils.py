import re
import json
import hashlib
import random
import string
import logging
from typing import List
from typing import Dict
from copy import deepcopy
from flask import g
from flask_babel import gettext as _
from flask_babel import Locale
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal
from secrets import token_hex
from urllib.parse import urljoin
from uuid import UUID
from werkzeug.exceptions import Unauthorized
from werkzeug.exceptions import Forbidden

import requests
from email_validator import validate_email as email_validator_function
from email_validator import EmailNotValidError
from usernames import is_safe_username
from usernames.reserved_words import _d as default_blacklist
from flask import request
from flask import session
from flask import current_app as app
from flask_babel import get_locale

from .exceptions import Auth54ValidationError
from .exceptions import AuthServiceNotRegistered
from .ecdsa_lib import sign_data
from .ecdsa_lib import verify_signature

KEY_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits


class APIJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder. Encoder for datetime objects, UUID and Decimal.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            rr = obj.isoformat()
            if obj.microsecond:
                rr = rr[:23] + rr[26:]
            if rr.endswith('+00:00'):
                rr = rr[:-6] + 'Z'
            return rr
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            if obj.utcoffset() is not None:
                raise ValueError(
                    'JSON can\'t represent timezone-aware times.')
            rr = obj.isoformat()
            if obj.microsecond:
                rr = rr[:12]
            return rr
        elif isinstance(obj, timedelta):
            return duration_iso_string(obj)
        elif isinstance(obj, (Decimal, UUID)):
            return str(obj)
        return super().default(obj)


def duration_iso_string(duration):
    """
    Helper function for proper translation of
    datetime.timedelta object into a string.
    """
    if duration < timedelta(0):
        sign = '-'
        duration *= -1
    else:
        sign = ''

    days, hours, mins, secs, msecs = _get_duration_components(
        duration)
    ms = '.{:06d}'.format(msecs) if msecs else ""
    return '{}P{}DT{:02d}H{:02d}M{:02d}{}S'.format(
        sign, days, hours, mins, secs, ms)


def _get_duration_components(duration):
    """
    Helper function for proper translation of
    datetime.timedelta object into a string.
    """
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds = seconds % 60

    hours = minutes // 60
    minutes = minutes % 60

    return days, hours, minutes, seconds, microseconds


def json_dumps(data, **kwargs):
    """
    Function like casual json.dumps, but using
    Django JSONEncoder upper as default class
    and passing all kwargs there.
    :param data: data for converting in the string
    :param kwargs: additional params
    :return: data in string format
    """
    return json.dumps(data, cls=APIJSONEncoder, **kwargs)


def generate_random_string(charset=KEY_CHARS, length=32):
    """
    Generates random string.
    :param charset: string of characters for generating
    :param length: int. length of result sting
    :return: string
    @subm_flow
    """
    return ''.join(random.choice(charset) for i in range(length))


def convert_datetime(value):
    return datetime.strftime(value, '%Y-%m-%d %H:%M:%S.%f')


def create_new_salt(user_info: dict, salt_for: str = None):
    """
    Generates a random salt and save it in database with uuid or public_key
    :param user_info: dictionary with key uuid or pub_key
    :param salt_for: string with argument what for we creating salt
    :return: salt: random generated hex string
    @subm_flow Generates a random salt and save it in database with uuid or public_key
    """
    salt = token_hex(16)

    if user_info.get('pub_key', None):
        if not is_valid_public_key(user_info.get('pub_key')):
            return None
        app.db.execute("INSERT INTO salt_temp(salt, pub_key, salt_for) VALUES (%s, %s, %s)",
                       [salt, user_info.get('pub_key'), salt_for])
    elif user_info.get('uuid', None):
        if not is_valid_uuid(user_info.get('uuid', None)):
            return None

        if not app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM actor WHERE uuid = %s)""",
                               [user_info.get('uuid')]).get('exists'):
            # local import only
            from .service_view import GetAndUpdateActor
            actor = GetAndUpdateActor(uuid=user_info.get('uuid')).update_actor()
            if not actor:
                return None

        app.db.execute("INSERT INTO salt_temp(salt, uuid, salt_for) VALUES (%s, %s::uuid, %s)",
                       [salt, user_info.get('uuid'), salt_for])
    elif user_info.get('qr_token', None):
        app.db.execute("INSERT INTO salt_temp(salt, qr_token, salt_for) VALUES (%s, %s, %s)",
                       [salt, user_info.get('qr_token'), salt_for])
    else:
        return None

    return salt


def get_user_salt(user_info: dict, salt_for: str = None):
    """
    Get salt that was sent to user to sign
    :param user_info: dictionary with key uuid or pub_key
    :param salt_for:  string with argument what for we creating salt
    :return: salt or None if not exists row
    @subm_flow Get salt that was sent to user to sign
    """

    if user_info.get('qr_token', None):
        salt = app.db.fetchone("""SELECT salt FROM salt_temp WHERE qr_token = %s AND uuid = %s AND salt_for=%s AND 
        created > timezone('utc', now()) ORDER BY created DESC LIMIT 1""",
                               [user_info.get('qr_token'), user_info.get('uuid'), salt_for])
        if not salt:
            salt = app.db.fetchone("""SELECT salt FROM salt_temp WHERE qr_token = %s AND uuid IS NULL AND salt_for=%s 
            AND created > timezone('utc', now()) ORDER BY created DESC LIMIT 1""",
                                   [user_info.get('qr_token'), salt_for])

            if not salt:
                return None

        return salt.get('salt')

    elif user_info.get('pub_key', None):
        if not is_valid_public_key(user_info.get('pub_key')):
            return None

        query ="""SELECT salt FROM salt_temp WHERE pub_key=%s AND salt_for=%s 
        AND created > timezone('utc', now()) ORDER BY created DESC LIMIT 1"""
        values = [user_info.get('pub_key'), salt_for]
    elif user_info.get('uuid', None):
        if not is_valid_uuid(user_info.get('uuid', None)):
            return None

        query = """SELECT salt FROM salt_temp WHERE uuid=%s::uuid AND salt_for=%s 
        AND created > timezone('utc', now()) ORDER BY created DESC LIMIT 1"""
        values = [user_info.get('uuid'), salt_for]
    else:
        return None

    salt = app.db.fetchone(query, values)
    if not salt:
        return None

    return salt.get('salt')


def delete_salt(user_info: dict):
    """
    Delete salt if it was used.
    :param user_info: dictionary with key uuid or pub_key
    :return: True if deleted, False if not
    """

    if user_info.get('pub_key', None):
        query = "DELETE FROM salt_temp WHERE pub_key=%s RETURNING salt"
        values = [user_info.get('pub_key')]
    elif user_info.get('uuid', None):
        query = "DELETE FROM salt_temp WHERE uuid=%s RETURNING salt"
        values = [user_info.get('uuid')]
    elif user_info.get('qr_token', None):
        query = "DELETE FROM salt_temp WHERE qr_token=%s RETURNING salt"
        values = [user_info.get('qr_token')]
    else:
        return False

    salt = app.db.fetchall(query, values)

    if not salt:
        return None

    return True


def update_salt_data(uuid: str, qr_token: str):
    """
    Update salt with setting actor uuid in database.
    :param uuid: actor uuid
    :param qr_token: qr token
    :return: updated salt or None
    """

    if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM actor WHERE uuid = %s)""", [uuid]).get('exists'):

        salt = app.db.fetchone("""UPDATE salt_temp SET uuid = %s WHERE qr_token = %s RETURNING *""", [uuid, qr_token])

        if not salt:
            return None

        return salt

    return None


def is_valid_uuid(uuid: str, version: int = None):
    """
    Check if uuid is valid UUID
    :param uuid: string uuid on test
    :param version: uuid version
    :return: True if valid else False
    @subm_flow
    """
    if not isinstance(uuid, str):
        try:
            uuid = str(uuid)
        except Exception as e:
            logging_message('Error while converting uuid in string')
            return False

    if version:
        try:
            uuid_obj = UUID(uuid, version=version)
        except (AttributeError, ValueError, TypeError):
            return False

        return str(uuid_obj) == uuid

    check_result = None
    for version in range(1, 6):
        try:
            uuid_obj = UUID(uuid, version=version)
        except (AttributeError, ValueError, TypeError):
            continue

        check_result = str(uuid_obj) == uuid
        if not check_result:
            continue
        else:
            return check_result

    return check_result


def is_valid_public_key(public_key: str):
    """
    Check if public key is valid by length and prefix
    :param public_key: string public key
    :return: True if valid else False
    @subm_flow
    """
    # Public key length if we using coordinates (04 prefix) is 130
    # symbols.
    if len(public_key) != 130:
        return False

    # Check whether public key contains hex characters only
    if not all(c in string.hexdigits for c in public_key):
        return False

    # We should check on 04 prefix cause ecdsa public key with
    # Elliptic Curve starts with prefix 04
    if not public_key.startswith('04'):
        return False
    return True


def get_public_key(uuid: str):
    """
    Getting user public key
    :param uuid: user uuid
    :return: initial_key, secondary keys: initial_key - primary user public key
    saved in registration process (PRIMARY), secondary_key - list of generated
    user public keys
    @subm_flow
    """
    secondary_keys = None
    data = app.db.fetchone("SELECT initial_key, secondary_keys FROM actor WHERE uuid=%s", [uuid])

    if not data:
        # Such user does not exists
        return None, None
    if data.get('secondary_keys'):
        secondary_keys = data.get('secondary_keys').values()

    initial_key = data.get('initial_key')
    return initial_key, secondary_keys


def get_apt54(uuid: str):
    """
    Send POST request on auth for getting apt54
    :param uuid: user uuid
    :return: apt54 or None
    @subm_flow
    """
    if app.config.get('AUTH_STANDALONE'):
        return get_apt54_locally(uuid)

    url = urljoin(get_auth_domain(internal=True), '/get_apt54/')
    data = dict(
        uuid=uuid,
        service_uuid=app.config['SERVICE_UUID']
    )

    # Request custom expiration date
    if not check_if_auth_service():
        expiration_period = get_custom_session_expiration_period(as_timedelta=False)
        if expiration_period:
            data['requested_expiration_period'] = expiration_period

    data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'], json_dumps(data, sort_keys=True))
    try:
        response = requests.post(url, json=data, headers=get_language_header())
    except Exception as e:
        logging_message('Auth is unreachable', status=500)
        return None, 500
    data = json.loads(response.content)
    if response.ok:
        if verify_apt54(data):
            return data, response.status_code

    return data, response.status_code


def get_apt54_locally(uuid: str):
    """
    Build apt54 locally
    :param uuid:
    :return: apt54 or None
    @subm_flow Build apt54 locally
    """
    from .actor import Actor
    from .actor import ActorNotFound
    try:
        actor = Actor.objects.get(uuid=uuid)
    except ActorNotFound:
        return None, 452

    data = json_dumps(actor.to_dict(), sort_keys=True)

    expiration_period = get_custom_session_expiration_period()
    if not expiration_period:
        expiration_period = timedelta(days=14)

    expiration = datetime.strftime(datetime.utcnow() + expiration_period,
                                   '%Y-%m-%d %H:%M:%S')
    signature = sign_data(app.config['SERVICE_PRIVATE_KEY'], data + expiration)
    response = dict(
        user_data=json.loads(data),
        expiration=expiration,
        signature=signature
    )
    return response, 200


def request_actor_from_auth_service(data):
    if app.config.get('AUTH_STANDALONE') or check_if_auth_service():
        return None
    request_data = data.copy()
    request_data['service_uuid'] = app.config.get('SERVICE_UUID')
    request_data['signature'] = sign_data(app.config['SERVICE_PRIVATE_KEY'], json_dumps(request_data, sort_keys=True))
    try:
        response = requests.post(
            urljoin(get_auth_domain(internal=True), '/service/get_actor_by_identificator/'),
            json=request_data,
            headers=get_language_header()
        )
        response_data = response.json()
    except Exception as e:
        logging_message(message="Error with getting actor from Auth service."
                                "\n Exception - %s" % (e), status=500)
    else:
        if actor := response_data.get('actor'):
            # Create user on client service with data from auth service
            try:
                query = "INSERT INTO actor SELECT * FROM jsonb_populate_record(null::actor, jsonb %s)"
                values = [json_dumps(actor)]
                app.db.execute(query, values)
            except Exception as e:
                logging_message(message="Error with creating user.\n"
                                        "Actor - %s\n Exception - %s" % (actor, e), status=500)
            else:
                return actor
    return None


def check_actor_is_banned(actor):
    if actor.is_banned and not actor.is_root:
        response = create_response_message(message=_("You are in ban group. "
                                                    "Please contact the administrator to set you role."), error=True)
        return response


def create_session_token(uuid, apt54, auxiliary_token=None, service_uuid=None, depended_info={}):
    while True:
        result = dict(
            session_token=generate_random_string(KEY_CHARS)
        )

        if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM service_session_token WHERE session_token=%s)""",
                           [result.get("session_token")]).get('exists'):
            continue

        app.db.execute("""INSERT INTO service_session_token(session_token, uuid, apt54, auxiliary_token, service_uuid) 
                          VALUES (%s, %s, %s, %s, %s)""",
        [result.get("session_token"), uuid, json_dumps(apt54), auxiliary_token, service_uuid or app.config['SERVICE_UUID']])

        if depended_info:
            make_session_in_depended_services(depended_info, result)

        return result


def create_session(user_data: dict, auxiliary_token: str = '', service_uuid: str = '', depended_info: dict = {}):
    """
    Session generation on service based on user_data
    :param user_data: dict. User's signature
    :param auxiliary_token: string value of generate salt
    :param service_uuid: target service uuid fir what session_token is creating
    :param depended_info: data for creation session on depended_services
    :return: session_token: str. Service session token
    @subm_flow Session generation on service based on user data
    """
    from .actor import Actor
    actor = Actor(user_data)
    if is_banned_result := check_actor_is_banned(actor):
        return is_banned_result

    expiration_period = get_custom_session_expiration_period()
    if not expiration_period:
        expiration_period = timedelta(days=14)
    expiration = datetime.strftime(datetime.utcnow() + expiration_period,
                            '%Y-%m-%d %H:%M:%S')
    # TODO add signature with service private key?
    apt54 = {
        'user_data': user_data,
        'expiration': expiration
    }

    result = create_session_token(
        actor.uuid, apt54,
        auxiliary_token=auxiliary_token,
        service_uuid=service_uuid,
        depended_info=depended_info
    )

    if result and app.config.get('SESSION_STORAGE', None) == 'SESSION' or app.config.get(
            'SESSION_STORAGE') is None:
        session['session_token'] = result.get("session_token")

    result['expiration'] = expiration
    return result


def create_session_with_apt54(apt54: dict, auxiliary_token: str = ''):
    """
    Session generation on service based on apt54
    :param apt54: dict. User's apt54
    :param auxiliary_token: temporary_session generated during Single-Sign-On
    :return: session_token: str. Service session token
    @subm_flow Session generation on service based on apt54
    """
    from .actor import Actor
    uuid = apt54['user_data'].get('uuid') if apt54.get('user_data') else apt54.get('uuid')
    actor = Actor.objects.get(uuid=uuid)
    if is_banned_result := check_actor_is_banned(actor):
        return is_banned_result

    result = create_session_token(
        actor.uuid, apt54,
        auxiliary_token=auxiliary_token,
    )
    return result


def get_depended_services_source(full_source=False):
    """
    Get depended services from app config
    If DYNAMIC_DEPENDED_SERVICES_ENABLED, get depended services from DYNAMIC_DEPENDED_SERVICES dict
    by HTTP_ORIGIN(front domain) as key.
    """
    dynamic_services = app.config.get('DYNAMIC_DEPENDED_SERVICES')
    if app.config.get('DYNAMIC_DEPENDED_SERVICES_ENABLED') and dynamic_services and isinstance(dynamic_services, dict):
        if not full_source:
            origin = request.environ.get('HTTP_ORIGIN', app.config.get('SERVICE_DOMAIN'))
            if origin in dynamic_services:
                return dynamic_services[origin]
        else:
            full_data = {}
            for source in dynamic_services.values():
                full_data.update(source)
            return full_data     
    elif services := app.config.get('DEPENDED_SERVICES'):
        if isinstance(services, dict):
            return services
    
    return {}


def get_salt_from_depended_services(data):
    """
    Get authentication salt from depended services
    """
    depended_services_info = {}
    if depended_services_source := get_depended_services_source():
        service_data = data
        service_data['step'] = 'identification'
        for name, domain in depended_services_source.items():
            try:
                service_response = requests.post(
                    urljoin(domain, "/auth/"),
                    json=service_data
                )
            except:
                pass
            else:
                if service_response.ok:
                    depended_services_info.update(
                        {
                            name: service_response.json()
                        }
                    )
    return depended_services_info


def make_session_in_depended_services(depended_info, autentication_result):
    """
    Send requests to depended services and get session tokens from them
    @subm_flow
    """
    for name, service_data in depended_info.items():
        try:
            depended_services_source =  get_depended_services_source(full_source=True)
            url = urljoin(depended_services_source.get(name.lower()), '/auth/' )
            autentication_result.update({
                name + "_session_token": dict(requests.post(url, json=service_data
                                        ).json()).get("session_token")
            }
            )
        except:
            pass


def get_session_token():
    """
    Get session token from request.
    :return: session_token or None in case if session_token is not present in cookies or request
    @subm_flow
    """
    session_token = None
    if 'Session-Token' in request.headers or 'session_token' in session:
        session_token = request.headers.get('Session-Token')
        if not session_token:
            session_token = session.get('session_token')

    return session_token


def get_session(session_token: str):
    """
    Get session by session_token
    :param session_token: token of the session
    :return: session object if exists
    """
    service_session_token= app.db.fetchone("""SELECT * FROM service_session_token WHERE session_token=%s""",
                                           [session_token])

    return service_session_token


def get_session_token_by_auxiliary(auxiliary_token: str = None):
    """
    Get session by auxiliary_token.
    :param auxiliary_token: string. Some token which we use to save session. Example: QR token = auxiliary token.
    :return: session
    """
    service_session_token = app.db.fetchone("""SELECT session_token FROM service_session_token 
    WHERE auxiliary_token=%s""", [auxiliary_token])

    return service_session_token


def verify_apt54(apt54: dict):
    """
    APT54 verification that user received it from auth and didn't change any data
    :param apt54: user APT54
    :return: verification result. True - verification passed, False - verification failed
    @subm_flow
    """
    signature = apt54.get('signature')
    user_data = json_dumps(apt54.get('user_data'), sort_keys=True)
    data = str(user_data) + str(apt54.get('expiration'))
    if app.config.get('AUTH_STANDALONE'):
        if not verify_signature(app.config['SERVICE_PUBLIC_KEY'], signature, data):
            return False
    else:
        if not verify_signature(app.config['AUTH_PUB_KEY'], signature, data):
            return False
    return True


def check_if_auth_service():
    """
    Checks if service auth or not.
    :return: boolean value. True - if service auth, False - if not
    @subm_flow Checks if service auth or not
    """
    salt = token_hex(16)
    signature = sign_data(app.config['SERVICE_PRIVATE_KEY'], salt)
    if app.config.get('AUTH_STANDALONE'):
        if not verify_signature(app.config['SERVICE_PUBLIC_KEY'], signature, salt):
            return False
    else:
        if not verify_signature(app.config['AUTH_PUB_KEY'], signature, salt):
            return False
    return True


def apt54_expired(expiration: str):
    """
    Check if apt54 expired
    :param expiration: apt54 expiration
    :return: True if expired, False if not
    @subm_flow
    """
    if datetime.utcnow() > datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S'):
        return True
    return False


def actor_exists(uuid: str):
    """
    Check if user exists on service
    :param uuid: user uuid we need to check
    :return: True if exists, False if not
    @subm_flow_sudm
    """
    # Check if user exists on service
    if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM actor WHERE uuid=%s)""", [uuid]).get('exists'):
        return True

    return False


def create_actor(apt54: dict):
    """
    Create actor on client service
    :param apt54: user apt54
    :return: actor if created or None if not
    @subm_flow_sudm
    """
    data = apt54.get('user_data')
    query = """INSERT INTO actor SELECT * FROM jsonb_populate_record(null::actor, jsonb %s::jsonb) RETURNING uuid"""
    values = [json_dumps(data)]
    try:
        actor_uuid = app.db.fetchone(query, values)
        query = """SELECT * FROM actor WHERE uuid = %s"""
        values = [actor_uuid.get('uuid')]
        actor = app.db.fetchone(query, values)
    except Exception as e:
        logging_message('Exception on creating actor! %s' % e)
        actor = None

    return actor


def update_user(apt54: dict):
    """
    Update user on client service
    :param apt54: user apt54
    @subm_flow
    """
    data = apt54.get('user_data')
    app.db.execute("""UPDATE actor SET uinfo = actor.uinfo::jsonb || %s::jsonb, initial_key = %s, secondary_keys = %s 
    WHERE actor.uuid = %s""", [json_dumps(data.get('uinfo')), data.get('initial_key'), data.get('secondary_keys'),
                               data.get('uuid')])


def create_response_message(message, error=False):
    """
    Create response dict with error status and just information message
    :param message: message text
    :param error: boolean flag. True - error message, False - information message
    :return: dict
    """
    if error:
        response = dict(
            error=True,
            error_message=message
        )
    else:
        response = dict(
            message=message
        )
    return response


def get_default_user_group():
    """
    Get default user group. By default user adds in this group
    :return: group
    @subm_flow
    """
    group = app.db.fetchone("""SELECT * FROM actor WHERE actor_type='group' AND uinfo->>'group_name'=%s""",
                            [app.config.get('DEFAULT_GROUP_NAME', 'DEFAULT')])
    return group


def generate_qr_token():
    """
    Generate random qr token
    :return: string
    """
    return generate_random_string(KEY_CHARS)


def get_static_group(group_name: str):
    """
    Get BAN or ADMIN or DEFAULT group.
    :param group_name: group name (BAN or ADMIN or DEFAULT)
    :return: group_uuid
    """
    group = app.db.fetchone("""SELECT uuid FROM actor WHERE actor_type='group' AND uinfo->>'group_name'=%s""",
                            [group_name])
    return group


def validate_email(email: str) -> None:
    """
    Validate passed email value.
    @subm_flow
    """
    try:
        valid = email_validator_function(email)
    except EmailNotValidError as e:
        logging_message(str(e))
        raise Auth54ValidationError('Invalid email')


def validate_login(login_value: str):
    """
    Validate passed login value.
    @subm_flow
    """
    banned_words = app.config.get('BANNED_WORDS_FOR_LOGIN', [])
    if banned_words:
        if isinstance(banned_words, str):
            banned_words = banned_words.splitlines()
        else:
            try:
                iter(banned_words)
            except TypeError:
                banned_words = []       
    if len(login_value) >= 3 and is_safe_username(
        login_value,
        whitelist=default_blacklist.splitlines(),
        blacklist=banned_words,
        max_length=36):
        return True
    return False


def validate_phone_number(phone_number: str):
    """
    Validate passed phone nubmer value.
    @subm_flow
    """
    if isinstance(phone_number, str) and len(phone_number) > 3 and phone_number[0] == '+':
        return True
    return False


def hash_md5(text: str):
    """
    Hash string with md5.
    Need for hashing password and password verification
    :param text: string
    :return: hashed string
    @subm_flow
    """
    hasher = hashlib.md5()
    hasher.update(text.encode('utf-8'))
    text = hasher.hexdigest()
    return text


def create_temporary_session(actor_uuid=None):
    """
    Create temporary session. Need for saving in cookies before redirect on auth.
    :return: temporary_session
    """
    while True:
        temporary_session = generate_random_string(KEY_CHARS)

        if app.db.fetchone("""SELECT EXISTS(SELECT 1 FROM temporary_session WHERE temporary_session=%s)""",
                           [temporary_session]).get('exists'):
            continue

        app.db.execute("""INSERT INTO temporary_session(temporary_session, service_uuid, actor_uuid) VALUES (%s, %s, %s)""",
                       [temporary_session, app.config['SERVICE_UUID'], actor_uuid])

        return temporary_session


def get_temporary_session_token():
    """
    Get temporary session token from cookies.
    :return: temporary_session_token
    """
    return request.cookies.get('temporary_session', None)


def get_temporary_session(temporary_session_token=None):
    """
    Get temporary session info from database
    :return: temporary_session
    """
    temporary_session_token = temporary_session_token or get_temporary_session_token()
    if not temporary_session_token:
        return None

    temporary_session = app.db.fetchone("""SELECT * FROM temporary_session WHERE temporary_session = %s 
    ORDER BY created DESC LIMIT 1 """, [temporary_session_token])

    return temporary_session


def delete_temporary_session(temporary_session: str = None):
    """
    Delete temporary session from database
    :return: None
    """
    if not temporary_session:
        temporary_session = get_temporary_session()

    app.db.execute("DELETE FROM temporary_session WHERE temporary_session = %s", [temporary_session])


def get_auth_domain(internal=False):
    """
    Get auth domain from database using AUTH PUBLIC KEY.
    :return: string
    """
    query = """SELECT
            uinfo->>'service_domain' AS service_domain,
            uinfo->>'internal_service_domain' AS internal_service_domain
            FROM actor WHERE initial_key = %s"""
    if app.config.get('AUTH_STANDALONE'):
        values = [app.config['SERVICE_PUBLIC_KEY']]
    else:
        values = [app.config['AUTH_PUB_KEY']]
    domain = app.db.fetchone(query, values)
    if not domain:
        raise AuthServiceNotRegistered
    if internal is True and app.config.get('INTERNAL_DOMAINS_ENABLED', True):
        return domain.get('internal_service_domain') or domain.get('service_domain')
    return domain.get('service_domain')


def print_error_cli(message: str = 'Some error occurred.', status: int = 400):
    """
    Print some error in console.
    :param message: message to write
    :param status: error status
    :return: None
    """
    print('-' * 35, 'ERROR %s' % status, '-' * 35)
    print(message)
    return


def get_service_locale():
    """
    Get locale code that service is using for this user by request.
    :return: string
    """
    try:
        locale = get_locale()
    except TypeError as e:
        logging_message('Error with getting locale - %s' % str(e))
        locale = request.cookies.get(app.config.get('LANGUAGE_COOKIE_KEY', None))
        if not locale or locale not in app.config.get('LANGUAGES', ['en', 'ru']):
            locale = request.accept_languages.best_match(app.config.get('LANGUAGES', ['en', 'ru']))
    except Exception as e:
        logging_message('Exception with getting locale - %s' % str(e))
        locale = 'en'

    return locale.language if isinstance(locale, Locale) else str(locale)


def get_language_header():
    """
    Create custom header with setting locale for requests on other services and receiving messages in set language
    :return: dict
    """
    return {"Http-Accept-Language": get_service_locale()}


def get_current_actor(raise_exception=True):
    """
    Get current actor from g or by session token or raise Unauthorized
    :param raise_exception: bool. Should service raise Unauthorized if there is no such actor.
    :return: actor or None or raise exception
    """
    from .actor import Actor
    from .actor import ActorNotFound

    if hasattr(g, 'actor'):
        return getattr(g, 'actor')

    session_token = get_session_token()
    if not session_token and not raise_exception:
        return None

    try:
        actor = Actor.objects.get_by_session(session_token=session_token)
        return actor
    except ActorNotFound:
        if not raise_exception:
            return None

    raise Unauthorized


def insert_update_query(
    order: List[str],
    conflict: List[str],
    permissions: List[Dict],
    subject: str,
):
    values: List = list()
    placeholders: List[str] = list()
    permissions = deepcopy(permissions)
    for permission in permissions:
        permission.update({"params": json_dumps(permission.get("params", {}))})
        values.extend([permission.get(item) for item in order])
        placeholders.append(f"({', '.join(['%s']*len(permission.keys()))})")

    query = f"""
        INSERT INTO
        {subject}_permaction({", ".join(order)})
        VALUES {", ".join(placeholders)}
        ON CONFLICT({", ".join(conflict)})
        DO UPDATE SET
        {', '.join([
            f'{key}=EXCLUDED.{key}'
            for key in order
        ])};
    """

    app.db.execute(query, values)


def insert_or_update_default_permaction(permissions: List[Dict]):
    order = [
        'permaction_uuid', 'service_uuid',
        'value', 'perm_type',
        'description', 'title', 'unions',
        'params'
    ]
    conflict = ['permaction_uuid', 'service_uuid']
    if permissions:
        insert_update_query(
            order=order,
            conflict=conflict,
            permissions=permissions,
            subject='default'
        )


def insert_or_update_actor_permaction(permissions: List[Dict]):
    order = [
        'permaction_uuid', 'service_uuid', 'actor_uuid',
        'value', 'params'
    ]
    conflict = ['permaction_uuid', 'service_uuid', 'actor_uuid']
    if permissions:
        insert_update_query(
            order=order,
            conflict=conflict,
            permissions=permissions,
            subject='actor'
        )


def insert_or_update_group_permaction(permissions: List[Dict]):
    order = [
        'permaction_uuid', 'service_uuid', 'actor_uuid',
        'value', 'weight', 'params'
    ]
    conflict = ['permaction_uuid', 'service_uuid', 'actor_uuid']
    if permissions:
        insert_update_query(
            order=order,
            conflict=conflict,
            permissions=permissions,
            subject='group'
        )


def delete_old_permactions(new_permactions):

    subjects = ["default", "group", "actor"]

    for subject in subjects:
        delete_not_exist_permactions(
            exist_permissions=new_permactions,
            subject=subject
        )


def delete_not_exist_permactions(
        exist_permissions: List[Dict],
        subject: str,
    ):
    """Delete all permactions except existing"""
    query = f"""
        DELETE FROM {subject}_permaction
        WHERE service_uuid = ANY(%s::uuid[])
        AND NOT permaction_uuid = ANY(%s::uuid[]);
    """

    service_uuids = list()
    permaction_uuids = list()

    for permaction in exist_permissions:
        service_uuids.append(permaction.get("service_uuid"))
        permaction_uuids.append(permaction.get("permaction_uuid"))

    values = list(set(service_uuids)), list(set(permaction_uuids))

    app.db.execute(query, values)


def ssh_to_https(remote_url):
    if remote_url[:3] == 'ssh':
        remote_url = 'https://' + remote_url[remote_url.index('@') + 1:]
        remote_url = re.sub(r':\d{1,5}', '', remote_url)

    remote_url = remote_url.replace('.git', '')

    return remote_url


def create_masquerading_session_token(
        actor_uuid :str,
        expiration_days :int = 1,
        expiration_hours :int = 0,
        expiration_minutes :int = 0,
        token_type :str = 'masquerading'
    ):
    from .actor import Actor, ActorNotFound

    if not actor_uuid or not is_valid_uuid(actor_uuid):
        raise ValueError("Invalid actor uuid was sent")
    
    try:
        actor = Actor.objects.get(uuid=actor_uuid)
    except ActorNotFound as e:
        if app.config.get('AUTH_STANDALONE') or check_if_auth_service():
            raise e
        from .service_view import GetAndUpdateActor
        GetAndUpdateActor(actor_uuid).update_actor()
        try:
            actor = Actor.objects.get(uuid=actor_uuid)
        except ActorNotFound:
            raise e
    
    if actor.actor_type not in ('user', 'classic_user'):
        raise ValueError("Invalid actor type")
    
    current_actor = get_current_actor()

    if actor.is_root:
        logging_message(f'Actor <{current_actor.uuid}> tried to masquerade root actor <{actor.uuid}>', 403)
        raise Forbidden('Permissions denied')
    elif actor.is_admin and not (current_actor.is_admin or current_actor.is_root):
        logging_message(f'Non-admin actor <{current_actor.uuid}> tried to masquerade admin actor <{actor.uuid}>', 403)
        raise Forbidden('Permissions denied')

    session_token = generate_random_string()
    expiration = datetime.strftime(datetime.utcnow() + timedelta(days=expiration_days, hours=expiration_hours, minutes=expiration_minutes),
                                    '%Y-%m-%d %H:%M:%S')
    masquerading_apt54 = {
        'expiration': expiration,
        'masquerade_performer_uuid': current_actor.uuid,
        'user_data': actor.to_dict()
    }

    app.db.execute("""INSERT INTO service_session_token(session_token, uuid, apt54, service_uuid, token_type) 
        VALUES (%s, %s, %s, %s, %s)""", 
        [session_token, actor_uuid, json_dumps(masquerading_apt54), app.config.get('SERVICE_UUID'), token_type])
    
    return session_token


def get_custom_session_expiration_period(period=None, as_timedelta=True):
    session_token_lifetime = app.config.get('SESSION_TOKEN_LIFETIME_DAYS') if period is None else period
    if session_token_lifetime:
        try:
            custom_expiration_period = timedelta(days=session_token_lifetime)
        except:
            logging_message(
                f"""Invalid value for SESSION_TOKEN_LIFETIME_DAYS - {session_token_lifetime}, 
                type - {type(session_token_lifetime)}. Default value was applied""",
            )
        else:
            return custom_expiration_period if as_timedelta else session_token_lifetime


def get_service_certificate(service_uuid: str, domain: str) -> True or str:
    result = True
    certificate = app.db.fetchone(
        """SELECT certificate as certificate
        FROM certificate WHERE service_uuid = %s AND domain=%s
        ORDER BY created DESC LIMIT 1;
        """, (service_uuid, domain))

    if certificate:
        result = f"/tmp/{service_uuid}"
        try:
            with open(result, "w") as file:
                file.write(certificate.get("certificate"))
        except Exception as e:
            logging_message(f'Error with writing certificate to tmp directory \n {e}')

    return result

def logging_message(message: str, level: str = 'error', status: int = 400, logger_name: str = 'auth_submodule') -> None:
    """ 
    Depends by settings write log file/print in concole message
    
    params:
        message: string to output in console/log
        level: log level, default 'error'
        status: if console and level 'error' provide status to func
        logger_name: Logging name if use not in submodule must be provide 
    """
    if not app.config.get('ECOSYSTEM54_LOGGING_MODULE_ENABLED'):
        if level == 'error':
            print_error_cli(message, status)
        else:
            print(message)
    else:
        try:
            logger = logging.getLogger(logger_name)
            method = getattr(logger, level)
            method(message)
        except AttributeError:
            logger.error(message)
