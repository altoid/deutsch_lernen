import mysql.connector.errors
from flask import Blueprint, current_app, request
from mysql.connector import connect
from dlernen import dlernen_json_schema
import requests
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


@bp.route('/api/<int:word_id>/attrkey', methods=['POST'])
def add_attributes(word_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        pprint(e)
        return "bad payload: %s" % e.message, 400

    # checks:
    # word_id exists
    # zero-length attrkey list is ok
    # attrvalue ids exist and belong to the word
    # new attrvalues are all strings len > 0.

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = """
            select attrkey, attribute_id
            from mashup_v where word_id = %(word_id)s
            """
            cursor.execute(sql, {'word_id': word_id})
            rows = cursor.fetchall()
            if len(rows) == 0:
                cursor.execute('rollback')
                return "no such word id:  %s" % word_id, 400

            defined_attrkeys = {r['attrkey'] for r in rows}
            payload_attrkeys = {a['attrkey'].strip() for a in payload['attributes']}

            undefined_attrkeys = payload_attrkeys - defined_attrkeys
            if len(undefined_attrkeys) > 0:
                wtf = ', '.join(undefined_attrkeys)
                message = "invalid attrkeys:  %s" % wtf
                cursor.execute('rollback')
                return message, 400

            payload_attrvalues = [a['attrvalue'].strip() for a in payload['attributes']]
            bad_attrvalues = list(filter(lambda x: not bool(x), payload_attrvalues))
            if len(bad_attrvalues) > 0:
                message = "attrkey values cannot be empty strings"
                cursor.execute('rollback')
                return message, 400

            # checks complete, let's do this
            rows_to_insert = []
            attrdict = {r['attrkey']: r['attribute_id'] for r in rows}
            for a in payload['attributes']:
                t = (attrdict[a['attrkey']], word_id, a['attrvalue'].strip())
                rows_to_insert.append(t)

            if rows_to_insert:
                # pprint(rows_to_insert)
                sql = """
                insert into word_attribute (attribute_id, word_id, attrvalue)
                values (%s, %s, %s)
                """
                cursor.executemany(sql, rows_to_insert)

            cursor.execute('commit')

            url = "%s/api/word/%s" % (current_app.config['DB_URL'], word_id)
            r = requests.get(url)
            results = r.json()

            return results

        except Exception as e:
            pprint(e)
            cursor.execute('rollback')
            return 'error adding attributes to word_id %s' % word_id, 500


