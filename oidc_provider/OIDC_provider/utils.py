from flask import current_app as app
from flask import request
from flask import make_response
from werkzeug.security import gen_salt
import datetime
from functools import wraps

from cryptography.fernet import Fernet

from .exceptions import InvalidClientCallbackError
from .exceptions import InvalidAuthCodeError

KEY = Fernet.generate_key()
CODE_LIFE_SPAN = 600


def verify_client(func):
    """
    This decorator is used for checking if client_id is registered in service.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
      client_id = request.args.get('client_id')

      with app.db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM oidc_client WHERE client_id=%s", (client_id,))
        client_count = cur.fetchone()

        if client_count.get("count") == 1:
          return func(*args, **kwargs)
        
        return make_response(
          {"error": "invalid client_id"},
          400
        )

    return wrapper


def verify_access_token(token):
  pass


def generate_authorization_code(client_id, nonce, redirect_uri, uuid):
  '''
  generates authorization code and save it in database
  :return: authorization_code string length of 32
  '''
  authorization_code = gen_salt(32)
  expiration = datetime.datetime.now() + datetime.timedelta(milliseconds=CODE_LIFE_SPAN)

  app.db.execute(
    '''
    INSERT INTO oidc_auth_code(auth_code, nonce, client_id, redirect_uri, uuid, expiration)
    VALUES (%s, %s, %s, %s, %s, %s)
    ''',
    [authorization_code, nonce, client_id, redirect_uri, uuid, expiration]
  )
  return authorization_code



def verify_authorization_code(authorization_code, redirect_uri):
  '''
  validates authorization code and remove this code from database
  return: false if authorization code is invalid,
          otherwise return record from oidc_auth_code table
  '''
  record = app.db.fetchone('SELECT * FROM oidc_auth_code WHERE auth_code = %s', [authorization_code])
  
  if not record:
    raise InvalidAuthCodeError('Send invalid or expired authorization code.')

  redirect_uri_in_record = record.get('redirect_uri')
  expiration = record.get('expiration')

  if redirect_uri != redirect_uri_in_record:
    raise InvalidClientCallbackError('Invalid callback uri.')

  app.db.execute('DELETE FROM oidc_auth_code WHERE auth_code = %s', [authorization_code])
  
  if expiration < datetime.datetime.now():
    raise InvalidAuthCodeError('Authorization code expired.')

  return record