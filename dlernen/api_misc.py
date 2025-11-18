from flask import Blueprint, request, current_app
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
    # TODO - make sure the word conforms to dlernen_json_schema.WORD_PATTERN
    word = request.args.get('word')

    if word:
        sql = """
        WITH pos_data
             AS (SELECT p.NAME pos_name,
                        p.id   pos_id,
                        a.attrkey,
                        a.id   AS attribute_id,
                        pf.sort_order
                 FROM   pos_form pf
                        INNER JOIN pos p
                                ON p.id = pf.pos_id
                        INNER JOIN attribute a
                                ON a.id = pf.attribute_id),
             word_data
             AS (SELECT word_id,
                        word,
                        attribute_id,
                        attrvalue,
                        attrvalue_id,
                        pos_id
                 FROM   mashup_v
                 WHERE  word = %(word)s)
        SELECT pd.pos_name,
               pd.pos_id,
               pd.attrkey,
               pd.attribute_id,
               pd.sort_order,
               wd.word,
               wd.word_id,
               wd.attrvalue,
               wd.attrvalue_id
        FROM   pos_data pd
               LEFT JOIN word_data AS wd
                      ON pd.attribute_id = wd.attribute_id
                         AND pd.pos_id = wd.pos_id 
        """
    else:
        sql = """
        SELECT p.NAME AS pos_name,
               p.id   AS pos_id,
               a.attrkey,
               a.id   AS attribute_id,
               pf.sort_order,
               NULL   AS word,
               NULL   AS word_id,
               NULL   AS attrvalue,
               NULL   AS attrvalue_id
        FROM   pos_form pf
               INNER JOIN pos p
                       ON p.id = pf.pos_id
               INNER JOIN attribute a
                       ON a.id = pf.attribute_id 
        """

    """
    fetch the part-of-speech info from the database and format it
    """
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if word:
            cursor.execute(sql, {'word': word})
        else:
            cursor.execute(sql)

        rows = cursor.fetchall()

        name_to_attrs = {}
        name_to_ids = {}
        pos_to_word_info = {}

        for r in rows:
            if r['pos_name'] not in name_to_attrs:
                name_to_attrs[r['pos_name']] = []
            if r['pos_name'] not in name_to_ids:
                name_to_ids[r['pos_name']] = r['pos_id']
            if r['pos_name'] not in pos_to_word_info:
                pos_to_word_info[r['pos_name']] = (r['word'], r['word_id'])
            name_to_attrs[r['pos_name']].append(
                {
                    "attrkey": r['attrkey'].casefold(),
                    "attribute_id": r['attribute_id'],
                    "sort_order": r['sort_order'],
                    "attrvalue": r['attrvalue'],
                    "attrvalue_id": r['attrvalue_id']
                }
            )

        result = []
        for k in name_to_attrs.keys():
            result.append(
                {
                    "pos_name": k.casefold(),
                    "pos_id": name_to_ids[k],
                    "word": pos_to_word_info[k][0],
                    "word_id": pos_to_word_info[k][1],
                    "attributes": name_to_attrs[k]
                }
            )

        jsonschema.validate(result, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

        return result


@bp.route('/api/pos_keyword_mappings')
def get_pos_keyword_mappings():
    # from the comprehensive pos structure, create mappings of attribute and POS names to their respective ids,
    # and vice versa.
    #
    # this is used for unit testing.  it is not intended for any client so its return value is not validated.

    pos_structure = get_pos()

    mappings = {
        "pos_names_to_ids": {
           x['pos_name']: x['pos_id'] for x in pos_structure
        },
        "attribute_names_to_ids": {
            y['attrkey']: y['attribute_id'] for x in pos_structure for y in x['attributes']
        },
        "pos_ids_to_names": {
            x['pos_id']: x['pos_name'] for x in pos_structure
        },
        "attribute_ids_to_names": {
            y['attribute_id']: y['attrkey'] for x in pos_structure for y in x['attributes']
        }
    }

    return mappings


@bp.route('/api/config')
def get_config():
    d = dict(current_app.config)

    # timedelta objects aren't serializable, so do this
    d['PERMANENT_SESSION_LIFETIME'] = d['PERMANENT_SESSION_LIFETIME'].total_seconds()

    return d, 200
