from flask import Blueprint, request, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import common
from contextlib import closing
from dlernen.dlernen_json_schema import ARRAY_PREFIX_VERB_RESPONSE_SCHEMA
from dlernen.decorators import js_validate_result

bp = Blueprint('api_verbs', __name__, url_prefix='/api/verbs')


@js_validate_result(ARRAY_PREFIX_VERB_RESPONSE_SCHEMA)
@bp.route('/prefix/<string:prefix>', methods=['GET'])
def get_verbs_by_prefix(prefix):
    if not prefix:
        return "invalid prefix", 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            word_id,
            grundverb_word_id,
            prefix_word_id,
            pos_name prefix_pos_name,
            extracted_prefix,
            prefix
        from verb_prefix_v
        where extracted_prefix = %s
        """

        cursor.execute(sql, (prefix,))
        rows = cursor.fetchall()

        result = [
            {
                'word_id': x['word_id'],
                'grundverb_word_id': x['grundverb_word_id'],
                'prefix_word_id': x['prefix_word_id'],
                'prefix_pos_name': x['prefix_pos_name'],
                'prefix': x['extracted_prefix']
            }
            for x in rows
        ]

        if not result:
            return "not found", 404

        return result


@js_validate_result(ARRAY_PREFIX_VERB_RESPONSE_SCHEMA)
@bp.route('/grundverb/<string:grundverb>', methods=['GET'])
def get_verbs_by_grundverb(grundverb):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            word_id,
            grundverb_word_id,
            prefix_word_id,
            pos_name prefix_pos_name,
            prefix
        from verb_prefix_v
        where grundverb = %s
        """

        cursor.execute(sql, (grundverb,))
        rows = cursor.fetchall()

        result = [
            {
                'word_id': x['word_id'],
                'grundverb_word_id': x['grundverb_word_id'],
                'prefix_word_id': x['prefix_word_id'],
                'prefix_pos_name': x['prefix_pos_name'],
                'prefix': x['prefix']
            }
            for x in rows
        ]

        if not result:
            return "not found", 404

        return result
