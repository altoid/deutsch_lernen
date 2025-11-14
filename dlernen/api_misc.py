from flask import Blueprint, current_app
from mysql.connector import connect
from dlernen import dlernen_json_schema
from pprint import pprint
from contextlib import closing
import jsonschema

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


@bp.route('/api/pos')
def get_pos():
    """
    fetch the part-of-speech info from the database and format it
    """
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select p.name, a.attrkey, pf.sort_order
        from pos_form pf
        inner join pos p on p.id = pf.pos_id
        inner join attribute a on a.id = pf.attribute_id;
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        temp_result = {}
        for r in rows:
            if r['name'] not in temp_result:
                temp_result[r['name']] = []
            temp_result[r['name']].append(
                {
                    "attrkey": r['attrkey'],
                    "sort_order": r['sort_order']
                }
            )

        result = []
        for k in temp_result.keys():
            result.append(
                {
                    "name": k.lower(),
                    "attributes": temp_result[k]
                }
            )

        jsonschema.validate(result, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

        return result


@bp.route('/api/config')
def get_config():
    d = dict(current_app.config)

    # timedelta objects aren't serializable, so do this
    d['PERMANENT_SESSION_LIFETIME'] = d['PERMANENT_SESSION_LIFETIME'].total_seconds()

    return d, 200
