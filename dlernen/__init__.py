from flask import Flask
import config


def create_app():
    app = Flask(__name__)
    app.secret_key = "ap.i*&(^ap1."
    app.config.from_object(config.Config)

    return app
