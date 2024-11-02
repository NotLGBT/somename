import json
from flask import Blueprint
from flask import request

from .decorators import data_parsing
from .utils import delete_salt
from .utils import logging_message
from .logger import configure_logs_for_module

# Base auth_perms blueprint
auth_submodule = Blueprint(name="auth_submodule", import_name=__name__, template_folder='templates',
                           static_url_path='/auth_perms/core/static', static_folder='static')


# Urls on apps in google market and appstore
ERP_APP_URL = dict(
    android='https://play.google.com/store/apps/details?id=ecosystem54.android',
    ios='https://apps.apple.com/us/app/ecosystem54/id1496286184'
)

configure_logs_for_module('auth_submodule')

@auth_submodule.after_request
@data_parsing
def after_request(response, **kwargs):
    # Delete salt that was used
    if request.method == 'POST' and request.path == '/auth/' and response.status_code == 200:
        data = kwargs.get('data')
        if 'signed_salt' in data:
            if 'uuid' in data:
                salt = delete_salt({'uuid': data.get('uuid')})
            elif 'qr_token' in data:
                salt = delete_salt({'qr_token': data.get('qr_token')})
            elif 'apt54' in data:
                apt54 = data['apt54']
                if isinstance(apt54, str):
                    try:
                        apt54 = json.loads(apt54)
                    except:
                        apt54 = {}
                salt = delete_salt({'uuid': apt54.get('user_data', {}).get('uuid')})
                if not salt:
                    salt = delete_salt({'pub_key': apt54.get('user_data', {}).get('initial_key')})
            else:
                salt = None

            if not salt:
                logging_message('ERROR with deleting salt. Everything ok. data - %s' % data)

    return response
