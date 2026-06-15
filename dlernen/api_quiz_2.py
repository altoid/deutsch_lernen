from flask import Blueprint, request, current_app, url_for
import requests
from mysql.connector import connect
from contextlib import closing
from dlernen import common
from dlernen.dlernen_json_schema import \
    ATTRIBUTES, \
    QUIZ_ANSWER_PAYLOAD_SCHEMA_2, \
    QUIZ_REPORT_RESPONSE_SCHEMA, \
    QUIZ_RESPONSE_SCHEMA_2, \
    ARRAY_QUIZ_RESPONSE_SCHEMA_2, \
    ARRAY_QUIZ_ANSWER_PAYLOAD_SCHEMA_2
from dlernen.decorators import js_validate_result, js_validate_payload
from pprint import pprint

bp = Blueprint('api_quiz_2', __name__, url_prefix='/api/quiz/v2')

DEFINED_QUERIES = {
    'random',
    'oldest_first',
    'crappy_score',  # raw score < 0.8
}


# for the various GET requests, we guarantee that all attributes returned for a word will have values for all
# attributes defined for the quiz.


@bp.route('/<string:quiz_key>')
def get_words(quiz_key):
    # optional arguments:  query

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        return "unimplemented", 501


@bp.route('/<string:quiz_key>/wordlist/<int:wordlist_id>')
def get_words_in_wordlist(quiz_key, wordlist_id):
    # optional arguments:  query, tag (0 or more)

    tags = request.args.getlist('tag')
    tags = list(set(tags))  # remove dups

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        return "unimplemented", 501


@js_validate_result(ARRAY_QUIZ_RESPONSE_SCHEMA_2)
def __construct_result(rows, word_id):
    attributes = [
        {
            'attribute_id': r['attribute_id'],
            'sort_order': r['sort_order'],
            'attrvalue': r['attrvalue']
        }
        for r in rows
    ]
    result = [
        {
            'quiz_id': rows[0]['quiz_id'],
            'word_id': word_id,
            ATTRIBUTES: attributes
        }
    ]
    return result


@bp.route('/<string:quiz_key>/word/<int:word_id>')
def get_single_word(quiz_key, word_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # checks:
        # - quiz key exists
        # - word id exists
        # - word is a candidate for the quiz
        # - all attributes defined for the quiz have values

        # - quiz key exists
        sql = """
        select id 
        from quiz
        where quiz_key = %(quiz_key)s
        """

        cursor.execute(sql, {'quiz_key': quiz_key})
        rows = cursor.fetchall()
        if not rows:
            message = "unknown quiz:  %s" % quiz_key
            return message, 404

        # - word id exists
        sql = """
        select id 
        from word
        where id = %(word_id)s
        """

        cursor.execute(sql, {'word_id': word_id})
        rows = cursor.fetchall()
        if not rows:
            message = "unknown word_id:  %s" % word_id
            return message, 404

        # - word is a candidate for the quiz
        sql = """
        select
            quiz_id,
            word_id,
            attribute_id,
            attrvalue,
            sort_order
        from quiz_candidate_v
        where 
            quiz_key = %(quiz_key)s
            and word_id = %(word_id)s
        """

        cursor.execute(sql, {
            'word_id': word_id,
            'quiz_key': quiz_key
        })
        rows = cursor.fetchall()
        if not rows:
            message = "word_id %s not a candidate for quiz %s" % (word_id, quiz_key)
            return message, 400

        # - all attributes defined for the quiz have values
        undefined_attrs = list(filter(lambda x: not x['attrvalue'], rows))
        if undefined_attrs:
            message = "missing attribute values for word %s" % word_id
            return message, 409

        result = __construct_result(rows, word_id)

        return result


@bp.route('/<string:quiz_key>', methods=['POST'])
def post_quiz_answers(quiz_key):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        return "unimplemented", 501
