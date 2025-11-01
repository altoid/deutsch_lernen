from flask import Blueprint, request, current_app
from mysql.connector import connect
from dlernen import quiz_sql, dlernen_json_schema, common
from contextlib import closing
import jsonschema

# /api/quiz and quiz_metadata endpoints are here.

bp = Blueprint('api_quiz', __name__)


def build_quiz_metadata(rows):
    result = {}
    for row in rows:
        if row['quiz_key'] not in result:
            result[row['quiz_key']] = {
                'quiz_id': row['quiz_id'],
                'quizname': row['quizname'],
                'quiz_key': row['quiz_key'],
                'attributes': []
            }
        result[row['quiz_key']]['attributes'].append(row['attrkey'])
    result = list(result.values())
    return result


@bp.route('/api/quiz')
def get_all_quizzes():
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select distinct quiz_id, quizname, quiz_key, attrkey
        from quiz_v
        """

        cursor.execute(sql)
        rows = cursor.fetchall()
        return build_quiz_metadata(rows)


@bp.route('/api/quiz/<int:quiz_id>')
def get_quiz_by_id(quiz_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select distinct quiz_id, quizname, quiz_key, attrkey
        from quiz_v
        where quiz_id = %s
        """

        cursor.execute(sql, (quiz_id,))
        rows = cursor.fetchall()
        if not rows:
            return "quiz %s not found" % quiz_id, 404

        return build_quiz_metadata(rows)[0]


@bp.route('/api/quiz/<string:quiz_key>')
def get_quiz_by_key(quiz_key):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select distinct quiz_id, quizname, quiz_key, attrkey
        from quiz_v
        where quiz_key = %s
        """

        cursor.execute(sql, (quiz_key,))
        rows = cursor.fetchall()
        if not rows:
            return "quiz %s not found" % quiz_key, 404

        return build_quiz_metadata(rows)[0]


@bp.route('/api/quiz_data/<string:quiz_key>')
def quiz_data(quiz_key):
    """
    given a quiz key, randomly pick from the dictionary one attrkey value to be quizzed.
    """

    word_ids = []
    wordlist_ids = request.args.get('wordlist_id')  # this will come in as a comma-separated string.
    if wordlist_ids:
        wordlist_ids = wordlist_ids.split(',')
        wordlist_ids = list(set(wordlist_ids))

        word_ids = common.get_word_ids_from_wordlists(wordlist_ids)

    query = quiz_sql.build_quiz_query(word_ids=word_ids)
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if wordlist_ids:
            cursor.execute(query, (quiz_key, *word_ids))
        else:
            cursor.execute(query, (quiz_key,))

        rows = cursor.fetchall()
        results_dict = {}

        for row in rows:
            keez = row.keys()
            if row['last_presentation']:
                row['last_presentation'] = row['last_presentation'].strftime("%Y-%m-%d %H:%M:%S")

            if row['word_id'] not in results_dict:
                results_dict[row['word_id']] = {
                    k: row.get(k) for k in keez & {
                        'qname',
                        'quiz_id',
                        'word_id',
                        'word'
                    }
                }
                results_dict[row['word_id']]['attributes'] = {}
            if row['attrkey'] not in results_dict[row['word_id']]['attributes']:
                results_dict[row['word_id']]['attributes'][row['attrkey']] = {
                    k: row.get(k) for k in keez & {
                        'correct_count',
                        'presentation_count',
                        'attrvalue',
                        'attribute_id',
                        'last_presentation'
                    }
                }
        result = list(results_dict.values())

    if not result:
        return "no testable attributes for quiz %s" % quiz_key, 404

    jsonschema.validate(result, dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA)

    return result


@bp.route('/api/quiz_data', methods=['POST'])
def post_quiz_answer():
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute('start transaction')
        update = """
            insert into quiz_score
            (quiz_id, word_id, attribute_id, presentation_count, correct_count)
            VALUES
            (%(quiz_id)s, %(word_id)s, %(attribute_id)s, %(presentation_count)s, %(correct_count)s)
            on duplicate key update
            presentation_count = values(presentation_count),
            correct_count = values(correct_count)
            """

        cursor.execute(update, request.form)
        cursor.execute('commit')

    return 'OK'
