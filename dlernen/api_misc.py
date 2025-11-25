from flask import Blueprint, current_app
from mysql.connector import connect
from pprint import pprint
from contextlib import closing

# miscellaneous /api endpoints are here.

bp = Blueprint('api_misc', __name__)


@bp.route('/healthcheck')
def dbcheck():
    try:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            return 'OK', 200
    except Exception as e:
        return str(e), 500


@bp.route('/api/gender_rules')
def gender_rules():
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        query = """
        select article, rule
        from gender_rule
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


@bp.route('/api/config')
def get_config():
    d = dict(current_app.config)

    # timedelta objects aren't serializable, so do this
    d['PERMANENT_SESSION_LIFETIME'] = d['PERMANENT_SESSION_LIFETIME'].total_seconds()

    return d, 200
