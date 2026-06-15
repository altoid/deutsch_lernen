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

SQL_WORDLIST = """
with candidate_word_id as
(
    select
        qc.quiz_id,
        qc.word_id,
        qc.word,
        qc.attribute_id,
        qc.attrvalue,
        qc.sort_order,
        ww.wordlist_id
        -- tag is not selected.  we want to filter with it, not see it.

    from quiz_candidate_v qc
    inner join wordlist_word ww
    on qc.word_id = ww.word_id

    where quiz_key = %(QUIZ_KEY)s
    and ww.wordlist_id = %(WORDLIST_ID)s

    -- for smart lists we have to give all the word ids, but there won't be any tags
),
incomplete_candidates as
(
    select distinct word_id
    from candidate_word_id
    where attrvalue is null
),
complete_candidates as
(
    select distinct word_id, wordlist_id
    from candidate_word_id
    where word_id not in (select word_id from incomplete_candidates)
)
select distinct
    candidate.quiz_id,
    candidate.word_id,
    candidate.word,
    candidate.attribute_id,
    candidate.attrvalue,
    candidate.sort_order,
    candidate.wordlist_id,
    ifnull(score.last_presentation, '1970-01-01 00:00:00') last_presentation,
    ifnull(score.correct_count, 0) correct_count,
    ifnull(score.presentation_count, 0) presentation_count,
    ifnull(score.correct_count / score.presentation_count, 0.0) raw_score

from candidate_word_id candidate
left join quiz_score_v score on score.quiz_id = candidate.quiz_id and score.word_id = candidate.word_id

where candidate.word_id in
    (select word_id from complete_candidates)
    
-- default query for client is 'random', so stir the shit
order by rand()
"""

SQL_WORDLIST_TAGS = """
"""


# for the various GET requests, we guarantee that all attributes returned for a word will have values for all
# attributes defined for the quiz.


@js_validate_result(ARRAY_QUIZ_RESPONSE_SCHEMA_2)
def __build_result(quiz_id, rows):
    # get the unique word ids in the order in which they appear in the query result.
    word_ids_in_order = []
    word_ids_seen = set()
    for r in rows:
        if r['word_id'] in word_ids_seen:
            continue

        word_ids_seen.add(r['word_id'])
        word_ids_in_order.append(r['word_id'])
    word_id_to_attributes = {x: [] for x in word_ids_seen}
    for r in rows:
        word_id_to_attributes[r['word_id']].append(
            {
                'attribute_id': r['attribute_id'],
                'sort_order': r['sort_order'],
                'attrvalue': r['attrvalue']
            }
        )
    result = [
        {
            'quiz_id': quiz_id,
            'word_id': x,
            ATTRIBUTES: sorted(word_id_to_attributes[x], key=lambda y: y['sort_order'])
        }
        for x in word_ids_in_order
    ]
    return result


@bp.route('/<string:quiz_key>/candidates/wordlist/<int:wordlist_id>')
def get_words_in_wordlist(quiz_key, wordlist_id):
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA_2
    # optional arguments:  query, tag (0 or more)

    query = request.args.get('query', 'random')
    tags = request.args.getlist('tag')
    tags = list(set(tags))  # remove dups

    # the query will get all the rows from quiz_candidate_v where a complete set of attributes exists for all the
    # words in the wordlist that are candidates for the quiz.  note that the attribute values have to exist for all
    # the attributes tested by the quiz, which is a subset of all the attributes defined for the part of speech.  for
    # example, the 'irregular_verbs' quiz does not look for first_person_singular, so this request could return words
    # for which first_person_singular is None.
    #
    # the query works by finding all the rows in quiz_candidate_v for the word/quiz.  from those we get the word ids
    # for every row with a null attribute value.  finally we select rows that do NOT have those word ids.
    #
    # to make the sql less awful, we will sort the rows here, not in the sql.  the query in the request determines the
    # how we sort.  the word_id in the first row thus obtained is the word that will be returned by the request.

    # checks:
    # - query is valid
    # - quiz_key is valid
    # - wordlist exists
    # - tags not allowed for smart list

    # - query is valid
    if query not in DEFINED_QUERIES:
        message = "unknown query:  %s" % query
        return message, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:

        # - quiz key is valid
        sql = """
        select id quiz_id
        from quiz
        where quiz_key = %(quiz_key)s
        """

        cursor.execute(sql, {'quiz_key': quiz_key})
        rows = cursor.fetchall()
        if not rows:
            message = "unknown quiz:  %s" % quiz_key
            return message, 404

        quiz_id = rows[0]['quiz_id']

        # wordlist exists
        list_metadata = common.get_wordlist_metadata(cursor, [wordlist_id])
        if not list_metadata:
            return "wordlist %s not found" % wordlist_id, 404

        # tags verboten with smart lists
        if tags and list_metadata['list_type'] == 'smart':
            message = "tags are verboten with smart lists"
            return message, 400

        # checks complete, let's do this.
        if tags:
            pass
        else:
            sql = SQL_WORDLIST
            cursor.execute(sql, {
                'WORDLIST_ID': wordlist_id,
                'QUIZ_KEY': quiz_key
            })

        rows = cursor.fetchall()

        # the connector is returning the raw score as a Decimal, have to convert it to float
        for r in rows:
            r['raw_score'] = float(r['raw_score'])

        if query == 'oldest_first':
            rows = sorted(rows, key=lambda x: x['last_presentation'])

        result = __build_result(quiz_id, rows)

        return result


@js_validate_result(QUIZ_RESPONSE_SCHEMA_2)
def __build_single_result(rows, word_id):
    attributes = [
        {
            'attribute_id': r['attribute_id'],
            'sort_order': r['sort_order'],
            'attrvalue': r['attrvalue']
        }
        for r in rows
    ]
    result = {
        'quiz_id': rows[0]['quiz_id'],
        'word_id': word_id,
        ATTRIBUTES: attributes
    }

    return result


@bp.route('/<string:quiz_key>/candidate/<int:word_id>')
def get_single_word(quiz_key, word_id):
    # returns a single instance of QUIZ_RESPONSE_SCHEMA_2

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

        result = __build_single_result(rows, word_id)

        return result


@bp.route('/<string:quiz_key>/scores', methods=['POST'])
def post_quiz_scores(quiz_key):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        return "unimplemented", 501
