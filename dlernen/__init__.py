from flask import Flask
from dlernen import config
from dlernen.dlernen import bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "ap.i*&(^ap1."
    app.config.from_object(config.Config)
    app.register_blueprint(bp)

    return app
