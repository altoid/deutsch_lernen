from flask import Blueprint, request, current_app, url_for
import requests
from mysql.connector import connect
import random
from contextlib import closing
import jsonschema
from dlernen import dlernen_json_schema, common
from pprint import pprint

# /api/quiz and quiz_metadata endpoints are here.

bp = Blueprint('api_quiz_v2', __name__, url_prefix='/api/v2/quiz')

# among the candidate words, give me the one with the crappiest score.  we use a weighted score
# based on the number of times the word has been presented.  a word with 1/1 correct is
# considered worse than one with 9/10 correct.  gives us the lowest-scoring word first.
#
# +---------+--------------+---------+---------------+--------------------+---------------+-----------+----------------+----------------+
# | quiz_id | attribute_id | word_id | attrvalue     | presentation_count | correct_count | raw_score | npresentations | weighted_score |
# +---------+--------------+---------+---------------+--------------------+---------------+-----------+----------------+----------------+
# |       4 |            6 |    1687 | verrate       |                  0 |             0 |    0.0000 |              0 |     0.00000000 |

COMMON_SQL = """
with
attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = '%(quiz_key)s'
),
words_to_test as (
select word, word_id, attrvalue, attribute_id from mashup_v
where attrvalue is not null
%(word_id_filter)s
),
word_attributes_to_test as (
select qa.quiz_id, qa.attribute_id, words_to_test.word_id, words_to_test.attrvalue, words_to_test.word
from attrs_for_quiz qa
inner join words_to_test on qa.attribute_id = words_to_test.attribute_id
),
"""

CRAPPY_SCORE_SQL = COMMON_SQL + """
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, wat.word,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
left join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
),
total_presentations as (
select sum(presentation_count) as npresentations
from word_scores
)

select 
    'crappy_score' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.correct_count,
    word_scores.presentation_count,
    word_scores.attribute_id,
    ifnull((presentation_count / npresentations) * raw_score, 0) as weighted_score
from word_scores, total_presentations
where raw_score < 0.95
or presentation_count <= 5   -- without this, if we get it right the first time we never see it again
order by raw_score, presentation_count desc
limit 1
"""

RARE_SQL = COMMON_SQL + """
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, wat.word,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
left join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
)

select 
    'rare' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.correct_count,
    word_scores.presentation_count,
    word_scores.attribute_id
from word_scores
where presentation_count <= 5
order by presentation_count
limit 1
"""

RANDOM_SQL = COMMON_SQL + """
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, wat.word,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
left join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
)

select 
    'random' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.correct_count,
    word_scores.presentation_count,
    word_scores.attribute_id
from word_scores
order by rand()
limit 1
"""

BEEN_TOO_LONG_SQL = COMMON_SQL + """
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, wat.word, qsc.last_presentation,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
INNER join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
)

select 
    'been_too_long' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.correct_count,
    word_scores.presentation_count,
    word_scores.attribute_id
from word_scores
where curdate() - interval 30 day > last_presentation
order by last_presentation
limit 1
"""

DEFINED_QUERIES = {
    'crappy_score',
    'been_too_long',
    'rare',
    'random'
}


@bp.route('/<string:quiz_key>')
def get_word_to_test(quiz_key):
    wordlist_ids = request.args.getlist('wordlist_id')

    # possible values for query are:
    #
    # - crappy_score
    # - been_too_long
    # - rare (5 or fewer presentations)
    # - random
    #
    queries = request.args.getlist('query')
    if not queries:
        queries = DEFINED_QUERIES

    undefined_queries = {x for x in queries} - DEFINED_QUERIES
    if undefined_queries:
        return "unknown queries: %s" % ', '.join(undefined_queries), 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select quiz_key
        from quiz
        where quiz_key = %(quiz_key)s
        """

        cursor.execute(sql, {'quiz_key': quiz_key})
        rows = cursor.fetchall()
        if not rows:
            return "quiz %s not found" % quiz_key, 404

        word_id_filter = ""
        word_ids = None
        if wordlist_ids:
            word_ids = common.get_word_ids_from_wordlists(wordlist_ids, cursor)

            word_id_args = ['%s'] * len(word_ids)
            word_id_args = ', '.join(word_id_args)

            word_id_filter = " and word_id in (%(word_id_args)s) " % {'word_id_args': word_id_args}

        words_chosen = []

        if 'crappy_score' in queries:
            sql = CRAPPY_SCORE_SQL % {
                'quiz_key': quiz_key,
                'word_id_filter': word_id_filter
            }

            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            if rows:
                words_chosen.append(rows[0])

        if 'rare' in queries:
            sql = RARE_SQL % {
                'quiz_key': quiz_key,
                'word_id_filter': word_id_filter
            }

            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            if rows:
                words_chosen.append(rows[0])

        if 'been_too_long' in queries:
            sql = BEEN_TOO_LONG_SQL % {
                'quiz_key': quiz_key,
                'word_id_filter': word_id_filter
            }

            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            if rows:
                words_chosen.append(rows[0])

        if 'random' in queries:
            sql = RANDOM_SQL % {
                'quiz_key': quiz_key,
                'word_id_filter': word_id_filter
            }

            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            if rows:
                words_chosen.append(rows[0])

        if words_chosen:
            winner = random.choice(words_chosen)
            # if this is a noun, add its article to the response.
            url = url_for('api_word.get_word_by_id', word_id=winner['word_id'], _external=True)

            r = requests.get(url)
            if not r:
                return r.text, r.status_code

            word_info = r.json()
            if word_info['pos_name'].casefold() == 'noun':
                article = list(filter(lambda x: x['attrkey'] == 'article', word_info['attributes']))
                winner['article'] = article[0]['attrvalue']

            jsonschema.validate(winner, dlernen_json_schema.QUIZ_RESPONSE_SCHEMA)

            return winner

        return {}


@bp.route('/<string:quiz_key>', methods=['POST'])
def post_quiz_answer(quiz_key):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.QUIZ_ANSWER_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        message = "bad payload: %s" % e.message
        return message, 400

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

        cursor.execute(update, payload)
        cursor.execute('commit')

    return 'OK', 200
