import json
import asyncio 
import threading

from functools import wraps

from flask import request
from flask import current_app as app 
from flask_babel import gettext as _
from werkzeug.exceptions import Forbidden

from ..utils import verify_signature


def shared_only(func):
    """ 
    This decorator is used for check is this shared request 
    """
    
    @wraps(func)
    def inner(self, *args, **kwargs):
        data = request.json if request.is_json else dict(request.form) 
        if not data.get('service_uuid'):
            raise Forbidden(_('Permissions denied.'))
        if pub_key := app.db.fetchone("SELECT initial_key FROM actor WHERE uuid = %s AND actor_type = 'service';",
                                [data.get('service_uuid')]).get('initial_key'):
            if verify_signature(pub_key, data.pop('signature'), json.dumps(data)):
                return func(self, *args, **kwargs)
        raise Forbidden(_('Permissions denied.'))
    return inner

_loop = None        
        
def fire_and_forget(f):
    """
    Decorator for sending request with asyncio and without waiting response.
    """
    
    def wrapped(*args, **kwargs):
        global _loop 
        if _loop is None:
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, daemon=True).start()
        _loop.call_soon_threadsafe(asyncio.create_task, f(*args, **kwargs))
    
    return wrapped
