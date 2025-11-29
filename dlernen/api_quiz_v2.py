from flask import Blueprint, request, current_app
from mysql.connector import connect
import random
from contextlib import closing
import jsonschema
from pprint import pprint
from common import get_word_ids_from_wordlists

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

CRAPPY_SCORE_SQL = """
with
attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = '%(quiz_key)s'
),
words_to_test as (
select wa.* from word_attribute wa
%(word_id_filter)s
),
word_attributes_to_test as (
select qa.quiz_id, qa.attribute_id, words_to_test.word_id, words_to_test.attrvalue from attrs_for_quiz qa
inner join words_to_test on qa.attribute_id = words_to_test.attribute_id
),
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue,
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

select 'crappy_score' qname, word_scores.*, total_presentations.*,
ifnull((presentation_count / npresentations) * raw_score, 0) as weighted_score
from word_scores, total_presentations
order by weighted_score, presentation_count desc
limit 1
"""

RARE_SQL = """
with
attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = '%(quiz_key)s'
),
words_to_test as (
select wa.* from word_attribute wa
%(word_id_filter)s
),
word_attributes_to_test as (
select qa.quiz_id, qa.attribute_id, words_to_test.word_id, words_to_test.attrvalue from attrs_for_quiz qa
inner join words_to_test on qa.attribute_id = words_to_test.attribute_id
),
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
left join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
)

select 'rare' qname, word_scores.* from word_scores
where presentation_count <= 5
order by presentation_count
limit 1
"""

BEEN_TOO_LONG_SQL = """
with
attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = '%(quiz_key)s'
),
words_to_test as (
select wa.* from word_attribute wa
%(word_id_filter)s
),
word_attributes_to_test as (
select qa.quiz_id, qa.attribute_id, words_to_test.word_id, words_to_test.attrvalue from attrs_for_quiz qa
inner join words_to_test on qa.attribute_id = words_to_test.attribute_id
),
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, qsc.last_presentation,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
INNER join quiz_score qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
)

select 'been_too_long' qname, word_scores.* from word_scores
where curdate() - interval 30 day > last_presentation
order by last_presentation
limit 1
"""

DEFINED_QUERIES = {
    'crappy_score',
    'been_too_long',
    'rare'
}


@bp.route('/<string:quiz_key>')
def get_word_to_test(quiz_key):
    wordlist_ids = request.args.getlist('wordlist_id')

    # possible values for query are:
    #
    # - crappy_score
    # - been_too_long
    # - rare (5 or fewer presentations)
    #
    queries = request.args.getlist('query')
    if not queries:
        queries = DEFINED_QUERIES

    undefined_queries = {x for x in queries} - DEFINED_QUERIES
    if undefined_queries:
        return "unknown queries: %s" % ', '.join(undefined_queries), 400

    result = {
        # 'wordlist_ids': wordlist_ids,
        # 'query': queries,
        # 'quiz_key': quiz_key,
        'rows': [],
    }

    words_chosen = []

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
            word_ids = get_word_ids_from_wordlists(wordlist_ids, cursor)

            word_id_args = ['%s'] * len(word_ids)
            word_id_args = ', '.join(word_id_args)

            word_id_filter = " where word_id in (%(word_id_args)s) " % {'word_id_args': word_id_args}

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

        # result['words_chosen'] = words_chosen
        result['winner'] = random.choice(words_chosen)

    return result, 200
