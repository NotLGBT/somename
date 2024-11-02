import settings
from flask import Flask
from auth_perms import AuthPerms
from auth_perms.core.manage import init_manager
# Not best practice

app = Flask(__name__)
app.config.from_object(settings)
AuthPerms(app=app, settings_module=settings, config_mode=settings.CONFIG_MODE, is_manager=True)
manager = init_manager(app)

if __name__ == '__main__':
    manager.run()