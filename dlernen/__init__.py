import werkzeug.exceptions
from flask import Flask, render_template
from dlernen import config
from dlernen.dlernen import bp as dlernen_bp
from dlernen.dlernen_relation import bp as dlernen_relation_bp

from dlernen.api_misc import bp as api_misc_bp
from dlernen.api_misc import bp as api_misc_bp
from dlernen.api_wordlist import bp as api_wordlist_bp
from dlernen.api_wordlist_tag import bp as api_wordlist_tag_bp
from dlernen.api_word import bp as api_word_bp
from dlernen.api_words import bp as api_words_bp
from dlernen.api_pos import bp as api_pos_bp
from dlernen.api_quiz import bp as api_quiz_bp
from dlernen.api_relation import bp as api_relation_bp
from dlernen.api_verbs import bp as api_verbs_bp

from dlernen.app_patch_words import bp as app_patch_words_bp
from dlernen.app_quiz import bp as app_quiz_bp
from dlernen.app_quiz_defs import bp as app_quiz_defs_bp


class DLException(werkzeug.exceptions.HTTPException):
    def __init__(self, message=None, response=None):
        # response is the object that is returned by requests.get|put|post|delete.  we'll use it in the error page.
        super().__init__()
        self.message = message
        self.response = response
        if self.response is not None:
            self.code = response.status_code
        else:
            self.code = 400


def create_app():
    app = Flask(__name__)
    app.secret_key = "ap.i*&(^ap1."
    app.config.from_object(config.Config)

    app.register_blueprint(dlernen_bp)
    app.register_blueprint(dlernen_relation_bp)

    app.register_blueprint(api_misc_bp)
    app.register_blueprint(api_quiz_bp)
    app.register_blueprint(api_wordlist_bp)
    app.register_blueprint(api_wordlist_tag_bp)
    app.register_blueprint(api_word_bp)
    app.register_blueprint(api_words_bp)
    app.register_blueprint(api_pos_bp)
    app.register_blueprint(api_relation_bp)
    app.register_blueprint(api_verbs_bp)

    app.register_blueprint(app_patch_words_bp)
    app.register_blueprint(app_quiz_bp)
    app.register_blueprint(app_quiz_defs_bp)

    app.aborter.mapping[400] = DLException
    app.aborter.mapping[404] = DLException
    app.aborter.mapping[500] = DLException

    @app.errorhandler(DLException)
    # stacking decoratoors is ok
    def dl_error_handler(dlexception):
        # abort() will create a DLException which winds up here.

        message = dlexception.message if dlexception.message else ''
        if dlexception.response is not None:
            if message:
                message = '%s:  %s [%s]' % (message, dlexception.response.text, dlexception.code)
            else:
                message = '%s [%s]' % (dlexception.response.text, dlexception.code)

        return render_template("error.html",
                               message=message,
                               status_code=dlexception.code)

    return app
