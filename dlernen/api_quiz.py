from flask import Blueprint, request, current_app, url_for
import requests
from mysql.connector import connect
import random
from contextlib import closing
import jsonschema
from dlernen import dlernen_json_schema, common
from pprint import pprint

# /api/quiz and quiz_metadata endpoints are here.

bp = Blueprint('api_quiz', __name__, url_prefix='/api/quiz')

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
    select word, word_id, attrkey, attrvalue, attribute_id 
    from mashup_v
    where attrvalue is not null
    %(word_id_filter)s
),
word_attributes_to_test as (
    select 
        qa.quiz_id, qa.attribute_id, words_to_test.word_id, 
        words_to_test.attrkey, words_to_test.attrvalue, 
        words_to_test.word
    from attrs_for_quiz qa
    inner join words_to_test on qa.attribute_id = words_to_test.attribute_id
),
word_scores as
(
select wat.quiz_id, wat.attribute_id, wat.word_id, wat.attrvalue, wat.word, wat.attrkey,
    qsc.last_presentation,
    ifnull(qsc.presentation_count, 0) presentation_count,
    ifnull(qsc.correct_count, 0) correct_count,
    ifnull(qsc.correct_count / qsc.presentation_count, 0) raw_score
from word_attributes_to_test wat
left join quiz_score_v qsc
    on wat.quiz_id = qsc.quiz_id
    and wat.attribute_id = qsc.attribute_id
    and wat.word_id = qsc.word_id
),
total_presentations as (
    select sum(presentation_count) as npresentations
    from word_scores
)
"""

CRAPPY_SCORE_SQL = COMMON_SQL + """
select 
    'crappy_score' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.attrkey,
    word_scores.attribute_id
from word_scores, total_presentations
where raw_score < 0.8
or presentation_count <= 5   -- without this, if we get it right the first time we never see it again
order by raw_score, presentation_count
limit 1
"""

# get the word we have seen least recently.
# this is the only one of the quiz query that is guaranteed to get every word, if we run it enough times.
OLDEST_FIRST_SQL = COMMON_SQL + """
select 
    'oldest_first' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.attrkey,
    word_scores.attribute_id
from word_scores
order by last_presentation
limit 1
"""

# quiz all the words where raw score < 100%
IMPERFECT_SCORE_SQL = COMMON_SQL + """
select 
    'imperfect' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.attrkey,
    word_scores.attribute_id
from word_scores
where raw_score < 1.00
order by last_presentation
limit 1
"""

RARE_SQL = COMMON_SQL + """
select 
    'rare' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.attrkey,
    word_scores.attribute_id
from word_scores
where presentation_count <= 5
order by presentation_count
limit 1
"""

RANDOM_SQL = COMMON_SQL + """
select 
    'random' query_name, 
    word_scores.word,
    word_scores.word_id,
    word_scores.quiz_id,
    word_scores.attrvalue,
    word_scores.attrkey,
    word_scores.attribute_id
from word_scores
order by rand()
limit 1
"""

REPORT_SQL = COMMON_SQL + """
select
    word_scores.word,
    word_scores.attrkey,
    word_scores.word_id,
    word_scores.correct_count,
    word_scores.presentation_count,
    raw_score * 100 AS raw_score,
    ifnull((presentation_count / npresentations) * raw_score, 0) as weighted_score,
    ifnull(last_presentation, '--') last_presentation
from word_scores, total_presentations
order by raw_score, presentation_count
"""

DEFINED_QUERIES = {
    'crappy_score': CRAPPY_SCORE_SQL,
    'rare': RARE_SQL,
    'random': RANDOM_SQL,
    'imperfect': IMPERFECT_SCORE_SQL,
    'oldest_first': OLDEST_FIRST_SQL,
}


def run_quiz_query(cursor, query, quiz_key, word_id_filter, word_ids):
    if query in DEFINED_QUERIES:
        sql = DEFINED_QUERIES[query] % {
            'quiz_key': quiz_key,
            'word_id_filter': word_id_filter
        }

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()
        if rows:
            return rows[0]


@bp.route('/<string:quiz_key>/word/<int:word_id>')
def get_all_attr_values_for_quiz(quiz_key, word_id):
    # the route has the useless 'word' component to avoid a collision with the route for
    # get_word_to_test_single_wordlist.

    # checks:
    #
    # - quiz_key exists
    # - word_id exists

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

        sql = """
        select id 
        from word
        where id = %(word_id)s"""

        cursor.execute(sql, {'word_id': word_id})
        rows = cursor.fetchall()
        if not rows:
            return "word_id %s not found" % word_id, 404

        # checks complete, let's do this

        sql = """
        select
            q.id quiz_id,
            m.attrvalue, 
            m.word, 
            m.word_id, 
            m.attribute_id, 
            m.attrkey
        from quiz q
        inner join quiz_structure qs on q.id = qs.quiz_id
        inner join attribute a on a.id = qs.attribute_id
        inner join mashup_v m on qs.attribute_id = m.attribute_id

        where
        q.quiz_key = %(quiz_key)s
        and m.word_id = %(word_id)s
        """

        cursor.execute(sql, {'word_id': word_id, 'quiz_key': quiz_key})
        rows = cursor.fetchall()

        # rows may be empty.  that's ok.
        jsonschema.validate(rows, dlernen_json_schema.QUIZ_RESPONSE_SCHEMA)

        return rows


@bp.route('/<string:quiz_key>/<int:wordlist_id>')
def get_word_to_test_single_wordlist(quiz_key, wordlist_id):
    tags = request.args.getlist('tag')

    # possible values for query are keys in DEFINED_QUERIES above
    query = request.args.get('query', 'oldest_first')
    if query not in DEFINED_QUERIES.keys():
        return "unknown query: %s" % query, 400

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

        r = requests.get(url_for('api_wordlist.get_wordlist',
                                 wordlist_id=wordlist_id,
                                 tag=tags,
                                 _external=True))
        if not r:
            return r.text, r.status_code

        wordlist = r.json()
        word_ids = [x['word_id'] for x in wordlist['known_words']]

        if word_ids:
            word_id_args = ['%s'] * len(word_ids)
            word_id_args = ', '.join(word_id_args)

            word_id_filter = " and word_id in (%(word_id_args)s) " % {'word_id_args': word_id_args}

            word_chosen = run_quiz_query(cursor, query, quiz_key, word_id_filter, word_ids)

            if word_chosen:
                # if this is a noun, add its article to the response.
                url = url_for('api_word.get_word_by_id', word_id=word_chosen['word_id'], _external=True)

                r = requests.get(url)
                if not r:
                    return r.text, r.status_code

                word_info = r.json()
                if word_info['pos_name'].casefold() == 'noun':
                    article = list(filter(lambda x: x['attrkey'] == 'article', word_info['attributes']))
                    word_chosen['article'] = article[0]['attrvalue']

                result = [word_chosen]
                jsonschema.validate(result, dlernen_json_schema.QUIZ_RESPONSE_SCHEMA)

                return result

        return []


@bp.route('/<string:quiz_key>')
def get_word_to_test(quiz_key):
    wordlist_ids = request.args.getlist('wordlist_id')
    wordlist_ids = list(map(int, wordlist_ids))

    # possible values for query are keys in DEFINED_QUERIES above
    query = request.args.get('query', 'oldest_first')

    if query not in DEFINED_QUERIES.keys():
        return "unknown query: %s" % query, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # check that quiz_key exists
        sql = """
        select quiz_key
        from quiz
        where quiz_key = %(quiz_key)s
        """

        cursor.execute(sql, {'quiz_key': quiz_key})
        rows = cursor.fetchall()
        if not rows:
            return "quiz %s not found" % quiz_key, 404

        # check that wordlist ids exist.  if any are undefined, reject the whole request.
        if wordlist_ids:
            # NB:  executemany won't work with select, only with DML statements.

            arglist = ['%s'] * len(wordlist_ids)
            sql = """
            select id as wordlist_id
            from wordlist
            where id in (%(arglist)s)
            """ % {'arglist': ', '.join(arglist)}

            cursor.execute(sql, wordlist_ids)
            rows = cursor.fetchall()

            given_wordlist_ids = set(wordlist_ids)
            found_wordlist_ids = {x['wordlist_id'] for x in rows}
            unknown_wordlist_ids = given_wordlist_ids - found_wordlist_ids
            if unknown_wordlist_ids:
                message = "undefined wordlist ids:  %s" % ', '.join(list(map(str, list(unknown_wordlist_ids))))
                return message, 404

        word_id_filter = ""
        word_ids = []
        if wordlist_ids:
            word_ids = common.get_word_ids_from_wordlists(wordlist_ids, cursor)
            if word_ids:
                word_id_args = ['%s'] * len(word_ids)
                word_id_args = ', '.join(word_id_args)
                word_id_filter = " and word_id in (%(word_id_args)s) " % {'word_id_args': word_id_args}

        #     wordlist_ids and     word_ids  - we have nonempty wordlists, run the query
        #     wordlist_ids and not word_ids  - wordlists are empty, don't run the query
        # not wordlist_ids and     word_ids  - won't happen
        # not wordlist_ids and not word_ids  - whole dictionary, this case is legit

        word_chosen = {}

        if wordlist_ids and word_ids:
            word_chosen = run_quiz_query(cursor, query, quiz_key, word_id_filter, word_ids)

        if not wordlist_ids and not word_ids:
            word_chosen = run_quiz_query(cursor, query, quiz_key, word_id_filter, word_ids)

        if word_chosen:
            # if this is a noun, add its article to the response.
            url = url_for('api_word.get_word_by_id', word_id=word_chosen['word_id'], _external=True)

            r = requests.get(url)
            if not r:
                return r.text, r.status_code

            word_info = r.json()
            if word_info['pos_name'].casefold() == 'noun':
                article = list(filter(lambda x: x['attrkey'] == 'article', word_info['attributes']))
                word_chosen['article'] = article[0]['attrvalue']

            result = [word_chosen]
            jsonschema.validate(result, dlernen_json_schema.QUIZ_RESPONSE_SCHEMA)

            return result

        return []


@bp.route('/answer', methods=['POST'])
def post_quiz_answer():
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.QUIZ_ANSWER_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        message = "bad payload: %s" % e.message
        return message, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute('start transaction')
        update = """
            insert into quiz_score_event
            (quiz_id, word_id, attribute_id, correct)
            VALUES
            (%(quiz_id)s, %(word_id)s, %(attribute_id)s, %(correct)s)
            """

        cursor.execute(update, payload)
        cursor.execute('commit')

    return 'OK', 200


@bp.route('/report/<string:quiz_key>/<int:wordlist_id>')
def get_report(quiz_key, wordlist_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select quiz_key, id AS quiz_id
        from quiz
        where quiz_key = %(quiz_key)s
        """

        cursor.execute(sql, {'quiz_key': quiz_key})
        rows = cursor.fetchall()
        if not rows:
            return "quiz %s not found" % quiz_key, 404

        quiz_id = rows[0]['quiz_id']

        # check that the wordlist_id is real
        sql = """
        select id
        from wordlist
        where id = %(wordlist_id)s
        """
        cursor.execute(sql, {'wordlist_id': wordlist_id})
        wordlist_row = cursor.fetchall()
        if not wordlist_row:
            return "wordlist %s not found" % wordlist_id, 404

        word_ids = common.get_word_ids_from_wordlists([wordlist_id], cursor)

        word_id_args = ['%s'] * len(word_ids)
        word_id_args = ', '.join(word_id_args)

        word_id_filter = " and word_id in (%(word_id_args)s) " % {'word_id_args': word_id_args}

        sql = REPORT_SQL % {
            'quiz_key': quiz_key,
            'word_id_filter': word_id_filter
        }

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()

        result = {
            "wordlist_id": wordlist_id,
            "quiz_key": quiz_key,
            "quiz_id": quiz_id,
            "scores": rows
        }

        jsonschema.validate(result, dlernen_json_schema.QUIZ_REPORT_RESPONSE_SCHEMA)

        return result
