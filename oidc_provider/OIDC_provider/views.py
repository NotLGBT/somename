from flask import Blueprint, request, redirect, url_for, make_response
from flask import current_app as app
from flask.views import MethodView
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import jwt
import datetime


from local_settings import SERVICE_DOMAIN
from auth_perms.core.decorators import token_required
from auth_perms.core.utils import get_current_actor

from .utils import  verify_client
from .utils import generate_authorization_code
from .utils import verify_authorization_code
from .exceptions import UnsupportedResponceTypeError
from .exceptions import MissingParamsError
from .exceptions import InvalidAuthCodeError
from .exceptions import ServerError
from actions.synapse_actions import CanLoginInSynapse


bp = Blueprint('openid', __name__)


with open('OIDC_provider/keys/private.pem', 'rb') as pr_key:
    private_key = serialization.load_pem_private_key(
        pr_key.read(),
        password=None
    )

with open('OIDC_provider/keys/public.pem', 'rb') as pub_key:
    public_key = serialization.load_pem_public_key(
        pub_key.read(),
        backend=default_backend
    )


class AuthorizationView(MethodView):
    @verify_client
    def get(self):
        '''
        Performs Authentication of the End-User

        :param data: client_id, state, scope, redirect_uri and response_type
        :return: redirect to login view with params response_type, scope, client_id, redirect_uri, state
        '''
        
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        scope = request.args.get('scope')
        response_type = request.args.get('response_type')

        if not all([client_id, redirect_uri, response_type]):
            raise MissingParamsError('Missing parameters! Expected parameters: client_id, redirect_uri, response_type')

        if response_type != 'code':
            raise UnsupportedResponceTypeError(f'Unsupported response type: {response_type}')

        return redirect(
            url_for(
                'auth_submodule.authorization',
                response_type=response_type, 
                scope=scope, 
                client_id=client_id, 
                redirect_uri=redirect_uri, 
                state=state
            )
        )


class AuthorizationCodeView(MethodView):
    def dispatch_request(self):
        CanLoginInSynapse().execute()
        return super().dispatch_request()

    @token_required
    def get(self):
        '''
        called after successfull authorization,
        generates authorization code and
        redirect to synapse callback path
        '''
        
        state = request.cookies.get('state')
        redirect_uri = request.cookies.get('redirect_uri')
        client_id = request.cookies.get('client_id')
        nonce = request.cookies.get('nonce')
        uuid = get_current_actor().uuid

        if not all([state, client_id, redirect_uri, nonce]):
            raise MissingParamsError('Missing parameters! Expected parameters: state, client_id, redirect_uri and nonce')

        code = generate_authorization_code(client_id, nonce, redirect_uri, uuid)
        
        return redirect(f"{redirect_uri}?code={code}&state={state}")


class TokenView(MethodView):
    def post(self):
        '''
        Obtaining an access token and an ID token
        :param data: grant_type, code, redirect_uri, client_id
        :return dict with id_token, access_token, token_type and expires_in
        '''

        grant_type = request.form.get('grant_type')
        code=request.form.get('code')
        redirect_uri = request.form.get('redirect_uri')

        authinfo = verify_authorization_code(code, redirect_uri)

        if not authinfo or grant_type != 'authorization_code':
            raise InvalidAuthCodeError('Send invalid or expired authorization code')

        data = app.db.fetchone('''SELECT uinfo FROM actor WHERE uuid = %s''', [authinfo.get('uuid')])

        uinfo = data['uinfo']
        id_token = self.generate_token({
            'sub': uinfo['email'],
            'name': f"{uinfo['first_name']}  {uinfo['last_name']}",
            'given_name': uinfo['email'].split('@')[0],
            'nonce': authinfo.get('nonce'),
            'azp': authinfo.get('client_id')
        })

        access_token = self.generate_token({
            'sub': uinfo['email'],
            'nonce': authinfo.get('nonce'),
            'azp': authinfo.get('client_id')
        })
        
        return make_response({
            'id_token': id_token,
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 300
        }, 200)
    

    def generate_token(self, payload):
        payload.update({
            'iss': SERVICE_DOMAIN,
            'aud': SERVICE_DOMAIN,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'scope': 'openid',
        })

        return jwt.encode(
                payload,
                private_key,
                algorithm='RS256'
            )
    

class JwksView(MethodView):
    def get(self):
        '''
        The JSON Web Key Set (JWKS), set of keys containing the public keys used to verify any JSON Web Token
        '''

        # getting key params
        if isinstance(public_key, rsa.RSAPublicKey):
            numbers = public_key.public_numbers()
            n = base64.urlsafe_b64encode(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip("=")
            e = base64.urlsafe_b64encode(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip("=")
        
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "kid": "1234",  
            "alg": "RS256", 
            "n": n,
            "e": e,
        }

        return make_response({"keys": [jwk]}, 200)


class DescriptiveView(MethodView):
    def get(self):
        '''
        Returns the OpenID Connect configuration values
        '''
        
        config = {
            "issuer": SERVICE_DOMAIN,
            "authorization_endpoint": SERVICE_DOMAIN + url_for('openid.authorize'),
            "token_endpoint": SERVICE_DOMAIN  + url_for('openid.token'),
            "jwks_uri": SERVICE_DOMAIN + url_for('openid.jwks'),
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }

        return make_response(config, 200)