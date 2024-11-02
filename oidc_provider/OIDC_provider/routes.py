from flask import Blueprint
from flask import request
from flask import url_for
from flask import make_response
from flask import jsonify

from .views import AuthorizationView
from .views import AuthorizationCodeView
from .views import TokenView
from .views import JwksView
from .views import DescriptiveView

bp = Blueprint('openid', __name__)

#oidc endpoints
bp.add_url_rule('/oidc/authorize', view_func=AuthorizationView.as_view('authorize'))
bp.add_url_rule('/oidc/auth_code', view_func=AuthorizationCodeView.as_view('auth_code'))
bp.add_url_rule('/oidc/token', view_func=TokenView.as_view('token'))

# provider description endpoints
bp.add_url_rule('/.well-known/openid-configuration', view_func=DescriptiveView.as_view('openid-configuration'))
bp.add_url_rule('/.well-known/jwks', view_func=JwksView.as_view('jwks'))


@bp.after_request
def after_request(response):
    if request.path == url_for('openid.authorize') and response.status == '302 FOUND':
        response.set_cookie('state', request.args.get('state'))
        response.set_cookie('redirect_uri', request.args.get('redirect_uri'))
        response.set_cookie('client_id', request.args.get('client_id'))
        response.set_cookie('nonce', request.args.get('nonce'))
    return response


@bp.errorhandler(Exception)
def handle_bad_request(ex, status: int = 400):
    return make_response(jsonify({'error': ex.description}), ex.code)