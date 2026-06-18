from flask import Blueprint, request, current_app
from enum import StrEnum, auto
from mysql.connector import connect
from contextlib import closing
from dlernen import common
from dlernen.dlernen_json_schema import \
    ATTRIBUTES, \
    QUIZ_ANSWER_PAYLOAD_SCHEMA_2, \
    QUIZ_REPORT_RESPONSE_SCHEMA_2, \
    QUIZ_RESPONSE_SCHEMA_2, \
    ARRAY_QUIZ_RESPONSE_SCHEMA_2, \
    ARRAY_QUIZ_ANSWER_PAYLOAD_SCHEMA_2
from dlernen.decorators import js_validate_result, js_validate_payload
from pprint import pprint

bp = Blueprint('api_quiz_2', __name__, url_prefix='/api/quiz/v2')

#
# SELECTORS
#
# these order and filter the rows returned by __get_rows_for_candidates.  they have the following semantics:
#
# random -        randomize the rows returned by the query.  this is the default.
# oldest_first -  order by last_presentation.  null values of last_presentation sort first.
# imperfect -     where raw_score < 1.00
#                 order by last_presentation
# rare -          where presentation_count <= 5
#                 order by presentation_count, last_presentation
# crappy_sccore - where raw_score < 0.8
#                 or presentation_count <= 5   -- without this, if we get it right the
#                                              -- first time we never see it again
#                 order by raw_score, presentation_count, last_presentation
# never         - where FALSE                  -- for testing; always causes 0 results to be returned
#                 order by 1


# noinspection PyArgumentList
# this comment keeps pycharm from bitching about auto()
class Selector(StrEnum):
    RANDOM = auto()          # value will be 'random', i.e. lowercase only
    OLDEST_FIRST = auto()
    CRAPPY_SCORE = auto()
    IMPERFECT = auto()
    RARE = auto()
    NEVER = auto()
    DEFAULT = OLDEST_FIRST


def __placeholder_string(itr):
    return ','.join(['%s'] * len(itr))


# for the various GET requests, we guarantee that all attributes returned for a word will have values for all
# attributes defined for the quiz.
#
# a CANDIDATE word for a quiz is a part of speech whose attributes are a superset of the attributes defined for the
# quiz.  for example, the definitions quiz has the single attribute 'definition.'  any part of speech with a
# definition is a candidate for that quiz.  all of the verbs are candidates for the 'present_indicative' and
# 'irregular_verbs' quizzes.  no noun is a candidate for either of these quizzes.
#
# a COMPLETE CANDIDATE for a quiz is a part of speech that has values for all attributes defined for the quiz.  an
# INCOMPLETE CANDIDATE is a candidate with at least one null-valued attribute.
#

# the complete_and_incomplete_candidates functions return two sets of word ids: those that are complete
# candidates for the quiz and those that are incomplete candidates.  the first set is the complete candidates; the
# second is the incomplete ones.  these sets will be disjoint.


def __complete_and_incomplete_candidates(cursor, quiz_key, word_ids=None):
    # divide the list of word_ids into complete and incomplete candidates.  if word_ids is None, subdivide the whole
    # dictionary.
    #
    # caller must check:
    # - quiz_key is real.
    # - word_ids is nonempty.
    #

    if word_ids:
        sql = """
        select distinct word_id
        from quiz_candidate_v
        where quiz_key = %%s
        and word_id in (%(PLACEHOLDERS)s)
        """ % {
            'PLACEHOLDERS': __placeholder_string(word_ids)
        }

        query_args = [quiz_key] + word_ids

    else:
        sql = """
        select distinct word_id
        from quiz_candidate_v
        where quiz_key = %s
        """

        query_args = [quiz_key]

    cursor.execute(sql, query_args)
    rows = cursor.fetchall()
    if not rows:
        return set(), set()

    candidate_word_ids = {r['word_id'] for r in rows}

    sql = """
    select distinct word_id
    from quiz_candidate_v
    where quiz_key = %%s
    and word_id in (%(PLACEHOLDERS)s)
    and attrvalue is null
    """ % {
        'PLACEHOLDERS': __placeholder_string(candidate_word_ids)
    }

    cursor.execute(sql, [quiz_key] + list(candidate_word_ids))
    rows = cursor.fetchall()

    incomplete_candidates = {x['word_id'] for x in rows}
    complete_candidates = candidate_word_ids - incomplete_candidates

    return complete_candidates, incomplete_candidates


def __complete_and_incomplete_candidates_in_wordlists(cursor, quiz_key, wordlist_ids, tags=None):
    # divide the candidate words in the given wordlist into complete/incomplete.  filter by the given tags.  it's up
    # to the caller to ensure that the tags exist in the wordlist.
    #
    # the wordlist_ids are assumed to point to valid wordlists.
    #
    # tags will be ignored if there is more than one wordlist_id.

    word_ids = common.get_word_ids_from_wordlists(cursor, wordlist_ids)
    complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates(cursor, quiz_key, word_ids)

    if tags and len(wordlist_ids) == 1:
        sql = """
        select distinct word_id
        from tag
        where wordlist_id = %%s
        and tag in (%(PLACEHOLDERS)s)
        """ % {
            'PLACEHOLDERS': __placeholder_string(tags)
        }

        cursor.execute(sql, [wordlist_ids[0]] + tags)
        rows = cursor.fetchall()
        tagged_word_ids = {r['word_id'] for r in rows}

        complete_candidates = complete_candidates & tagged_word_ids
        incomplete_candidates = incomplete_candidates & tagged_word_ids

    return complete_candidates, incomplete_candidates


def __get_rows_for_candidates(cursor, candidate_word_ids, quiz_id, selector=Selector.DEFAULT):
    where = ''
    order_by = 'rand()'
    if selector == Selector.OLDEST_FIRST:
        order_by = 'last_presentation'
    elif selector == Selector.IMPERFECT:
        order_by = 'last_presentation'
        where = 'AND raw_score < 1.00'
    elif selector == Selector.RARE:
        order_by = 'presentation_count, last_presentation'
        where = 'AND presentation_count <= 5'
    elif selector == Selector.CRAPPY_SCORE:
        order_by = 'raw_score, presentation_count, last_presentation'
        where = 'AND (raw_score < 0.8 or presentation_count <= 5)'
    elif selector == Selector.NEVER:
        where = 'and FALSE'
        order_by = '1'
    elif selector == Selector.RANDOM:
        where = ''
        order_by = 'rand()'

    sql = """
        select
            word,
            word_id,
            quiz_id,
            attribute_id,
            sort_order,
            attrvalue,
            attrkey,
            last_presentation,
            correct_count,
            presentation_count,
            raw_score
        from quiz_candidate_v
        where quiz_id = %%s 
        %(WHERE)s
        and word_id in (%(PLACEHOLDERS)s)

        order by %(ORDER_BY)s
    """ % {
        'PLACEHOLDERS': __placeholder_string(candidate_word_ids),
        'ORDER_BY': order_by,
        'WHERE': where
    }

    cursor.execute(sql, [quiz_id] + list(candidate_word_ids))
    rows = cursor.fetchall()

    # the connector is returning the raw score as a Decimal, have to convert it to float
    for r in rows:
        r['raw_score'] = float(r['raw_score'])

    return rows


def __get_rows_for_report(cursor, candidate_word_ids, quiz_id):
    sql = """
        select
            word,
            word_id,
            quiz_id,
            attribute_id,
            sort_order,
            attrvalue,
            attrkey,
            ifnull(last_presentation, '--') last_presentation,
            correct_count,
            presentation_count,
            raw_score * 100 as raw_score
        from quiz_candidate_v
        where quiz_id = %%s 
        and word_id in (%(PLACEHOLDERS)s)
    """ % {
        'PLACEHOLDERS': __placeholder_string(candidate_word_ids),
    }

    cursor.execute(sql, [quiz_id] + list(candidate_word_ids))
    rows = cursor.fetchall()

    # the connector is returning the raw score as a Decimal, have to convert it to float
    for r in rows:
        r['raw_score'] = float(r['raw_score'])

    return rows


def __get_articles_for_word_ids(cursor, quiz_key, word_ids):
    # if this quiz does NOT test for articles, then get the articles for every candidate word that has one.
    # return a dict mapping word_id to article.

    result = {}

    sql = """
    select quiz_key, quiz_id, attrkey from quiz q 
    inner join quiz_structure qs on q.id = qs.quiz_id 
    inner join attribute a on a.id = qs.attribute_id 
    where quiz_key = %(QUIZ_KEY)s and attrkey = 'article';
    """

    cursor.execute(sql, {
        'QUIZ_KEY': quiz_key
    })
    rows = cursor.fetchall()

    if word_ids and not rows:
        # this quiz is NOT testing for articles, so we can present them.

        sql = """
        select word_id, attrvalue from mashup_v 
        where word_id in (%(PLACEHOLDERS)s)
        and attrkey='article'
        """ % {
            'PLACEHOLDERS': __placeholder_string(word_ids)
        }
        cursor.execute(sql, list(word_ids))
        rows = cursor.fetchall()
        result = {r['word_id']: r['attrvalue'] for r in rows}

    return result


@js_validate_result(ARRAY_QUIZ_RESPONSE_SCHEMA_2)
def __build_results(quiz_id, rows, word_ids_to_articles):
    # get the unique word ids in the order in which they appear in the query result.
    word_ids_in_order = []
    word_ids_seen = set()
    for r in rows:
        if r['word_id'] in word_ids_seen:
            continue

        word_ids_seen.add(r['word_id'])
        word_ids_in_order.append(r['word_id'])

    word_id_to_word = {r['word_id']: r['word'] for r in rows}

    word_id_to_attributes = {x: [] for x in word_ids_seen}
    for r in rows:
        word_id_to_attributes[r['word_id']].append(
            {
                'attrkey': r['attrkey'],
                'attribute_id': r['attribute_id'],
                'sort_order': r['sort_order'],
                'attrvalue': r['attrvalue']
            }
        )
    results = [
        {
            'quiz_id': quiz_id,
            'word_id': x,
            'word': word_id_to_word[x],
            ATTRIBUTES: sorted(word_id_to_attributes[x], key=lambda y: y['sort_order'])
        }
        for x in word_ids_in_order
    ]

    for r in results:
        if r['word_id'] in word_ids_to_articles:
            r['article'] = word_ids_to_articles[r['word_id']]

    return results


@bp.route('/<string:quiz_key>/candidates')
def get_words(quiz_key):
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA_2
    # optional arguments:  selector, wordlist_ids (multiple.  if none given use whole dictionary.)

    selector = request.args.get('selector', Selector.DEFAULT)
    wordlist_ids = request.args.getlist('wordlist_id')
    wordlist_ids = list(set(wordlist_ids))  # remove dups

    # checks:
    # - selector is valid
    # - quiz_key is valid

    # - selector is valid
    if selector not in Selector:
        message = "unknown selector:  %s" % selector
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

        # checks complete, let's do this.
        if wordlist_ids:
            complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates_in_wordlists(cursor,
                                                                                                           quiz_key,
                                                                                                           wordlist_ids)
        else:
            complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates(cursor, quiz_key)

        if not complete_candidates:
            if incomplete_candidates:
                message = "missing attribute values for candidate words"
                return message, 409

            message = "no candidates for quiz %s" % quiz_key
            return message, 400

        rows = __get_rows_for_candidates(cursor, complete_candidates, quiz_id, selector)
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_key, complete_candidates)

        results = __build_results(quiz_id, rows, word_ids_to_articles)

        return results


@bp.route('/<string:quiz_key>/candidates/wordlist/<int:wordlist_id>')
def get_words_in_wordlist(quiz_key, wordlist_id):
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA_2
    # optional arguments:  selector, tag (0 or more)

    selector = request.args.get('selector', Selector.DEFAULT)
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
    # to make the sql less awful, we will sort the rows here, not in the sql.  the selector in the request determines the
    # how we sort.  the word_id in the first row thus obtained is the word that will be returned by the request.

    # checks:
    # - selector is valid
    # - quiz_key is valid
    # - wordlist exists
    # - tags not allowed for smart list

    # - selector is valid
    if selector not in Selector:
        message = "unknown selector:  %s" % selector
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

        list_metadata = list_metadata[0]

        # tags verboten with smart lists
        if tags and list_metadata['list_type'] == 'smart':
            message = "tags are verboten with smart lists"
            return message, 400

        # checks complete, let's do this.
        complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates_in_wordlists(cursor,
                                                                                                       quiz_key,
                                                                                                       [wordlist_id],
                                                                                                       tags)

        if not complete_candidates:
            if incomplete_candidates:
                message = "missing attribute values for candidate words"
                return message, 409

            message = "no candidates for quiz %s" % quiz_key
            return message, 400

        rows = __get_rows_for_candidates(cursor, complete_candidates, quiz_id, selector)
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_key, complete_candidates)

        results = __build_results(quiz_id, rows, word_ids_to_articles)

        return results


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

        word_ids = [word_id]

        # these are sets
        complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates(cursor, quiz_key, word_ids)

        if not complete_candidates:
            if incomplete_candidates:
                message = "missing attribute values for word %s" % word_id
                return message, 409

            message = "word_id %s not a candidate for quiz %s" % (word_id, quiz_key)
            return message, 400

        rows = __get_rows_for_candidates(cursor, complete_candidates, quiz_id)
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_key, complete_candidates)

        results = __build_results(quiz_id, rows, word_ids_to_articles)

        return results[0]


@js_validate_result(QUIZ_REPORT_RESPONSE_SCHEMA_2)
def __get_report(cursor, quiz_id, candidate_word_ids, wordlist_id, quiz_key):

    rows = __get_rows_for_report(cursor, candidate_word_ids, quiz_id)

    result = {
        'wordlist_id': wordlist_id,
        'quiz_key': quiz_key,
        'quiz_id': quiz_id,
        'words': []
    }

    word_id_to_word_result = {}

    attr_keys_to_copy = {
        'attrkey',
        'attribute_id',
        'sort_order',
        'correct_count',
        'presentation_count',
        'last_presentation',
        'raw_score'
    }

    for r in rows:
        if r['word_id'] not in word_id_to_word_result:
            word_id_to_word_result[r['word_id']] = {
                'word': r['word'],
                'word_id': r['word_id'],
                'attributes': []
            }
        attr_score = {k: r[k] for k in attr_keys_to_copy if k in r}
        word_id_to_word_result[r['word_id']]['attributes'].append(attr_score)

    result['words'] = list(word_id_to_word_result.values())

    return result


@bp.route('/<string:quiz_key>/<int:wordlist_id>/report')
def get_report(quiz_key, wordlist_id):
    # checks:
    #
    # - quiz_key is valid
    # - wordlist exists

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

        completes, incompletes = __complete_and_incomplete_candidates_in_wordlists(cursor, quiz_key, [wordlist_id])

        if not completes:
            if incompletes:
                message = "missing attribute values for candidate words"
                return message, 409

            message = "no candidates for quiz %s" % quiz_key
            return message, 400

        result = __get_report(cursor, quiz_id, completes, wordlist_id, quiz_key)

        return result


@bp.route('/<string:quiz_key>/score', methods=['POST'])
@js_validate_payload(QUIZ_ANSWER_PAYLOAD_SCHEMA_2)
def post_quiz_score(quiz_key):
    payload = request.get_json()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute('start transaction')

        # make sure the payload makes sense
        sql = """
        select quiz_id, word_id, attribute_id
        from quiz_candidate_v
        where quiz_key = %(QUIZ_KEY)s
        and word_id = %(WORD_ID)s
        and attribute_id = %(ATTRIBUTE_ID)s
        """
        cursor.execute(sql, {
            'QUIZ_KEY': quiz_key,
            'WORD_ID': payload['word_id'],
            'ATTRIBUTE_ID': payload['attribute_id']
        })
        rows = cursor.fetchall()
        if not rows:
            message = "payload ain't right for quiz %s" % quiz_key
            cursor.execute('rollback')
            return message, 400

        payload['quiz_id'] = rows[0]['quiz_id']
        update = """
            insert into quiz_score_event
            (quiz_id, word_id, attribute_id, correct)
            VALUES
            (%(quiz_id)s, %(word_id)s, %(attribute_id)s, %(correct)s)
            """

        cursor.execute(update, payload)
        cursor.execute('commit')

        return 'OK', 201
