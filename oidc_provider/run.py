import settings
from flask import Flask
from auth_perms import AuthPerms
from OIDC_provider.routes import bp
from flask_cors import CORS
from flask import url_for

app = Flask(__name__)
app.config.from_object(settings)
app.register_blueprint(bp)
cors = CORS(app)

AuthPerms(app=app, settings_module=settings, config_mode=settings.CONFIG_MODE)


if __name__ == "__main__":
    app.run(port=5001, debug=True)