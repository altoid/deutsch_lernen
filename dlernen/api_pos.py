from flask import Blueprint, current_app
from mysql.connector import connect
from dlernen import dlernen_json_schema
from pprint import pprint
from contextlib import closing
import jsonschema


bp = Blueprint('api_pos', __name__, url_prefix='/api/pos')


def __get_pos(sql, args):
    """
    fetch the part-of-speech info from the database and format it
    """
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(sql, args)

        rows = cursor.fetchall()

        pos_name_to_attrs = {}
        pos_name_to_ids = {x['pos_name']: x['pos_id'] for x in rows}
        pos_to_word_info = {x['pos_name']: (x['word'], x['word_id']) for x in rows}

        for r in rows:
            if r['pos_name'] not in pos_name_to_attrs:
                pos_name_to_attrs[r['pos_name']] = []
            pos_name_to_attrs[r['pos_name']].append(
                {
                    "attrkey": r['attrkey'].casefold(),
                    "attribute_id": r['attribute_id'],
                    "sort_order": r['sort_order'],
                    "attrvalue": r['attrvalue']
                }
            )

        result = []
        for k in pos_name_to_attrs.keys():
            result.append(
                {
                    "pos_name": k.casefold(),
                    "pos_id": pos_name_to_ids[k],
                    "word": pos_to_word_info[k][0],
                    "word_id": pos_to_word_info[k][1],
                    "attributes": pos_name_to_attrs[k]
                }
            )

        jsonschema.validate(result, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

        return result


@bp.route('/<int:word_id>')
def get_pos_for_word_id(word_id):
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
                    pos_id
             FROM   mashup_v
             WHERE  word_id = %(word_id)s)
    SELECT pd.pos_name,
           pd.pos_id,
           pd.attrkey,
           pd.attribute_id,
           pd.sort_order,
           wd.word,
           wd.word_id,
           wd.attrvalue
    FROM   pos_data pd
           INNER JOIN word_data AS wd
                  ON pd.attribute_id = wd.attribute_id
                     AND pd.pos_id = wd.pos_id 
    """

    return __get_pos(sql, {'word_id': word_id})


@bp.route('/<string:word>')
def get_pos_for_word(word):
    # TODO - make sure the word conforms to dlernen_json_schema.WORD_PATTERN
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
           wd.attrvalue
    FROM   pos_data pd
           LEFT JOIN word_data AS wd
                  ON pd.attribute_id = wd.attribute_id
                     AND pd.pos_id = wd.pos_id 
    """

    return __get_pos(sql, {'word': word})


@bp.route('')
def get_pos():
    sql = """
    SELECT p.NAME AS pos_name,
           p.id   AS pos_id,
           a.attrkey,
           a.id   AS attribute_id,
           pf.sort_order,
           NULL   AS word,
           NULL   AS word_id,
           NULL   AS attrvalue
    FROM   pos_form pf
           INNER JOIN pos p
                   ON p.id = pf.pos_id
           INNER JOIN attribute a
                   ON a.id = pf.attribute_id 
    """

    return __get_pos(sql, None)


@bp.route('/keyword_mappings')
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


