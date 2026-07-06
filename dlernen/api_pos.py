from flask import Blueprint, current_app
from mysql.connector import connect
from dlernen.dlernen_json_schema import POS_STRUCTURE_RESPONSE_SCHEMA
from dlernen.decorators import js_validate_result
from pprint import pprint
from contextlib import closing


bp = Blueprint('api_pos', __name__, url_prefix='/api/pos')


##########################################################################################
#
# there are no ORDER BY clauses in the sql.  all the sorting is done by __get_pos.
#


@js_validate_result(POS_STRUCTURE_RESPONSE_SCHEMA)
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
                    "sort_order": r['sort_order'],
                    "attrvalue": r['attrvalue']  # might be None
                }
            )

        result = []
        for pos_name, attrs in pos_name_to_attrs.items():
            # sort the attributes by sort_order
            attrs = sorted(attrs, key=lambda x: x['sort_order'])
            result.append(
                {
                    "pos_name": pos_name,
                    "pos_id": pos_name_to_ids[pos_name],
                    "word": pos_to_word_info[pos_name][0],  # might be None
                    "word_id": pos_to_word_info[pos_name][1],  # might be None
                    "attributes": attrs
                }
            )

        # sort the results by pos_id.
        # FIXME - introduce a sort key for POS names in the database (pos table)
        result = sorted(result, key=lambda x: x['pos_id'])

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
