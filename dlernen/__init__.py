from flask import Flask
from dlernen import config
from dlernen.dlernen import bp as dlernen_bp

from dlernen.api_misc import bp as api_misc_bp
from dlernen.api_misc import bp as api_misc_bp
from dlernen.api_wordlist import bp as api_wordlist_bp
from dlernen.api_wordlist_tag import bp as api_wordlist_tag_bp
from dlernen.api_word import bp as api_word_bp
from dlernen.api_pos import bp as api_pos_bp
from dlernen.api_quiz import bp as api_quiz_bp

from dlernen.app_patch_words import bp as app_patch_words_bp
from dlernen.app_quiz import bp as app_quiz_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "ap.i*&(^ap1."
    app.config.from_object(config.Config)

    app.register_blueprint(dlernen_bp)
    app.register_blueprint(api_misc_bp)
    app.register_blueprint(api_quiz_bp)
    app.register_blueprint(api_wordlist_bp)
    app.register_blueprint(api_wordlist_tag_bp)
    app.register_blueprint(api_word_bp)
    app.register_blueprint(api_pos_bp)

    app.register_blueprint(app_patch_words_bp)
    app.register_blueprint(app_quiz_bp)

    return app
