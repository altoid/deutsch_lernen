from flask import Blueprint, request, current_app
from enum import StrEnum, EnumType
from mysql.connector import connect
from contextlib import closing
from dlernen import common
from dlernen.dlernen_json_schema import \
    ATTRIBUTES, \
    QUIZ_ANSWER_PAYLOAD_SCHEMA, \
    QUIZ_REPORT_RESPONSE_SCHEMA, \
    ARRAY_QUIZ_RESPONSE_SCHEMA
from dlernen.decorators import js_validate_result, js_validate_payload
from pprint import pprint

bp = Blueprint('api_quiz', __name__, url_prefix='/api/quiz')


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


def __create_selector_class():
    class_name = "Selector"
    bases = (StrEnum,)  # Base classes must be inside a tuple

    # 1. Prepare the specialized EnumDict namespace required by EnumType
    class_dict = EnumType.__prepare__(class_name, bases)

    # 2. Inject your database or static enum members
    selector_dict = {
        'RANDOM': 'random',
        'OLDEST_FIRST': 'oldest_first',
        'RARE': 'rare',
        'CRAPPY_SCORE': 'crappy_score',
        'IMPERFECT': 'imperfect',
        'NEVER': 'never',
    }
    selector_dict['DEFAULT'] = selector_dict['OLDEST_FIRST']

    # note:  class_dict is an _EnumDict.  the |= operator won't work, but .update() works fine.
    class_dict.update(selector_dict)

    # 3. Define and inject your custom class methods or properties
    # def welcome(self):
    #     return f"Access granted for role: {self.value}"
    #
    # class_dict["welcome"] = welcome

    # 4. Construct the class safely using EnumType
    selector_class = EnumType(class_name, bases, class_dict)

    return selector_class


Selector = __create_selector_class()

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
            'PLACEHOLDERS': common.placeholder_string(word_ids)
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

    # from the word_ids for potential candidates, look for words with at least one null attrvalue.
    sql = """
    select distinct word_id
    from quiz_candidate_v
    where quiz_key = %%s
    and word_id in (%(PLACEHOLDERS)s)
    and attrvalue is null
    """ % {
        'PLACEHOLDERS': common.placeholder_string(candidate_word_ids)
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

    word_ids = common.get_word_ids_from_wordlists(cursor, wordlist_ids)  # returns [] if wordlist_ids is degenerate
    complete_candidates, incomplete_candidates = __complete_and_incomplete_candidates(cursor, quiz_key, word_ids)

    if wordlist_ids and word_ids and tags:
        sql = """
        select distinct word_id
        from tag
        where wordlist_id in (%(WORDLIST_ID_PLACEHOLDERS)s)
        and word_id in (%(WORD_ID_PLACEHOLDERS)s)
        and tag in (%(TAG_PLACEHOLDERS)s)
        """ % {
            'WORDLIST_ID_PLACEHOLDERS': common.placeholder_string(wordlist_ids),
            'WORD_ID_PLACEHOLDERS': common.placeholder_string(word_ids),
            'TAG_PLACEHOLDERS': common.placeholder_string(tags)
        }

        cursor.execute(sql, wordlist_ids + word_ids + tags)
        rows = cursor.fetchall()
        tagged_word_ids = {r['word_id'] for r in rows}

        complete_candidates = complete_candidates & tagged_word_ids
        incomplete_candidates = incomplete_candidates & tagged_word_ids

    return complete_candidates, incomplete_candidates


def __get_rows_for_candidates(cursor, candidate_word_ids, quiz_id, selector=Selector.DEFAULT):
    if not candidate_word_ids:
        return []

    flavor = {
        Selector.OLDEST_FIRST: {
            'where': '',
            'order_by': 'last_presentation'
        },
        Selector.IMPERFECT: {
            'where': 'AND raw_score < 1.00',
            'order_by': 'last_presentation'
        },
        Selector.RARE: {
            'where': 'AND presentation_count <= 5',
            'order_by': 'presentation_count, last_presentation'
        },
        Selector.CRAPPY_SCORE: {
            'where': 'AND (raw_score < 0.8 or presentation_count <= 5)',
            'order_by': 'raw_score, presentation_count, last_presentation'
        },
        Selector.RANDOM: {
            'where': '',
            'order_by': 'rand()'
        },
        Selector.NEVER: {
            'where': 'and FALSE',
            'order_by': '1'
        },
    }
    
    sql = """
        select
            word,
            word_id,
            quiz_key,
            attribute_id,
            sort_order,
            attrvalue,
            attrkey,
            pos_name,
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
        'PLACEHOLDERS': common.placeholder_string(candidate_word_ids),
        'ORDER_BY': flavor[selector]['order_by'],
        'WHERE': flavor[selector]['where']
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
        'PLACEHOLDERS': common.placeholder_string(candidate_word_ids),
    }

    cursor.execute(sql, [quiz_id] + list(candidate_word_ids))
    rows = cursor.fetchall()

    # the connector is returning the raw score as a Decimal, have to convert it to float
    for r in rows:
        r['raw_score'] = float(r['raw_score'])

    return rows


def __get_articles_for_word_ids(cursor, quiz_id, word_ids):
    # if this quiz does NOT test for articles, then get the articles for every candidate word that has one.
    # return a dict mapping word_id to article.

    result = {}

    sql = """
    select quiz_key, quiz_id, attrkey from quiz q 
    inner join quiz_structure qs on q.id = qs.quiz_id 
    inner join attribute a on a.id = qs.attribute_id 
    where quiz_key = %(QUIZ_ID)s and attrkey = 'article';
    """

    cursor.execute(sql, {
        'QUIZ_ID': quiz_id
    })
    rows = cursor.fetchall()

    if word_ids and not rows:
        # this quiz is NOT testing for articles, so we can present them.

        sql = """
        select word_id, attrvalue from mashup_v 
        where word_id in (%(PLACEHOLDERS)s)
        and attrkey='article'
        """ % {
            'PLACEHOLDERS': common.placeholder_string(word_ids)
        }
        cursor.execute(sql, list(word_ids))
        rows = cursor.fetchall()
        result = {r['word_id']: r['attrvalue'] for r in rows}

    return result


@js_validate_result(ARRAY_QUIZ_RESPONSE_SCHEMA)
def __build_results(quiz_key, rows, word_ids_to_articles):
    # get the unique word ids in the order in which they appear in the query result.
    word_ids_in_order = []
    word_ids_seen = set()
    for r in rows:
        if r['word_id'] in word_ids_seen:
            continue

        word_ids_seen.add(r['word_id'])
        word_ids_in_order.append(r['word_id'])

    word_id_to_word_pos_name = {r['word_id']: (r['word'], r['pos_name']) for r in rows}

    attr_keys_to_copy = {
        'attrkey',
        'sort_order',
        'attrvalue'
    }
    word_id_to_attributes = {x: [] for x in word_ids_seen}
    for r in rows:
        word_id_to_attributes[r['word_id']].append(
            {k: r[k] for k in attr_keys_to_copy if k in r}
        )
    results = [
        {
            'quiz_key': quiz_key,
            'word_id': x,
            'word': word_id_to_word_pos_name[x][0],
            'pos_name': word_id_to_word_pos_name[x][1],
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
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA
    # optional arguments:  selector, wordlist_ids (multiple.  if none given use whole dictionary.)

    selector = request.args.get('selector', Selector.DEFAULT)
    quiz_key_enum = current_app.extensions.get('QuizKey')
    wordlist_ids = request.args.getlist('wordlist_id')
    wordlist_ids = list(set(map(int, wordlist_ids)))  # convert to int and remove dups

    # checks:
    # - selector is valid
    # - quiz_key is valid

    # - selector is valid
    if selector not in Selector:
        message = "unknown selector:  %s" % selector
        return message, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # make sure quiz key is valid
        try:
            quiz_id = quiz_key_enum.get_id(quiz_key)
        except ValueError:
            message = "invalid quiz_key:  %s" % quiz_key
            return message, 400

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
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_id, complete_candidates)

        results = __build_results(quiz_key, rows, word_ids_to_articles)

        return results


@bp.route('/<string:quiz_key>/incomplete_candidates')
def get_incomplete_words(quiz_key):
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA.  returns empty list if nothing found.
    # optional arguments:  wordlist_ids (multiple.  if none given use whole dictionary.)

    quiz_key_enum = current_app.extensions.get('QuizKey')

    wordlist_ids = request.args.getlist('wordlist_id')
    wordlist_ids = list(set(map(int, wordlist_ids)))  # convert to int and remove dups

    # checks:
    # - quiz_key is valid

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:

        # - quiz key is valid
        try:
            quiz_id = quiz_key_enum.get_id(quiz_key)
        except ValueError:
            message = "invalid quiz_key:  %s" % quiz_key
            return message, 404

        # checks complete, let's do this.
        if wordlist_ids:
            _, incomplete_candidates = __complete_and_incomplete_candidates_in_wordlists(cursor,
                                                                                         quiz_key,
                                                                                         wordlist_ids)
        else:
            _, incomplete_candidates = __complete_and_incomplete_candidates(cursor, quiz_key)

        rows = __get_rows_for_candidates(cursor, incomplete_candidates, quiz_id)
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_id, incomplete_candidates)

        results = __build_results(quiz_key, rows, word_ids_to_articles)

        return results


@bp.route('/<string:quiz_key>/candidates/wordlist/<int:wordlist_id>')
def get_words_in_wordlist(quiz_key, wordlist_id):
    # returns ARRAY_QUIZ_RESPONSE_SCHEMA
    # optional arguments:  selector, tag (0 or more)

    selector = request.args.get('selector', Selector.DEFAULT)
    quiz_key_enum = current_app.extensions.get('QuizKey')

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
    # to make the sql less awful, we will sort the rows here, not in the sql.  the selector in the request determines
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
        try:
            quiz_id = quiz_key_enum.get_id(quiz_key)
        except ValueError:
            message = "invalid quiz_key:  %s" % quiz_key
            return message, 404

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
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_id, complete_candidates)

        results = __build_results(quiz_key, rows, word_ids_to_articles)

        return results


@bp.route('/<string:quiz_key>/candidate/<int:word_id>')
def get_single_word(quiz_key, word_id):
    # returns a single instance of QUIZ_RESPONSE_SCHEMA

    quiz_key_enum = current_app.extensions.get('QuizKey')

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # checks:
        # - quiz key exists
        # - word id exists
        # - word is a candidate for the quiz
        # - all attributes defined for the quiz have values

        # - quiz key exists
        try:
            quiz_id = quiz_key_enum.get_id(quiz_key)
        except ValueError:
            message = "invalid quiz_key:  %s" % quiz_key
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
        word_ids_to_articles = __get_articles_for_word_ids(cursor, quiz_id, complete_candidates)

        results = __build_results(quiz_key, rows, word_ids_to_articles)

        return results[0]


@js_validate_result(QUIZ_REPORT_RESPONSE_SCHEMA)
def __get_report(cursor, candidate_word_ids, wordlist_id, quiz_key):
    quiz_key_enum = current_app.extensions.get('QuizKey')

    quiz_id = quiz_key_enum.get_id(quiz_key)
    rows = __get_rows_for_report(cursor, candidate_word_ids, quiz_id)

    result = {
        'wordlist_id': wordlist_id,
        'quiz_key': quiz_key,
        'words': []
    }

    word_id_to_word_result = {}

    attr_keys_to_copy = {
        'attrkey',
        'sort_order',
        'correct_count',
        'presentation_count',
        'raw_score',
        'last_presentation',
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

    for k, v in word_id_to_word_result.items():
        v['attributes'] = sorted(v['attributes'], key=lambda x: x['sort_order'])

    result['words'] = list(sorted(word_id_to_word_result.values(), key=lambda x: x['word'].lower()))

    return result


@bp.route('/<string:quiz_key>/report/<int:wordlist_id>')
def get_report(quiz_key, wordlist_id):
    # checks:
    #
    # - quiz_key is valid
    # - wordlist exists

    tags = request.args.getlist('tag')
    quiz_key_enum = current_app.extensions.get('QuizKey')

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # - quiz key is valid
        if quiz_key not in quiz_key_enum:
            message = "invalid quiz_key:  %s" % quiz_key
            return message, 404

        # wordlist exists
        list_metadata = common.get_wordlist_metadata(cursor, [wordlist_id])
        if not list_metadata:
            return "wordlist %s not found" % wordlist_id, 404

        completes, incompletes = __complete_and_incomplete_candidates_in_wordlists(cursor, quiz_key, [wordlist_id],
                                                                                   tags=tags)

        if not completes:
            if incompletes:
                message = "missing attribute values for candidate words"
                return message, 409

            message = "no candidates for quiz %s" % quiz_key
            return message, 400

        result = __get_report(cursor, completes, wordlist_id, quiz_key)

        return result


@bp.route('/<string:quiz_key>/score', methods=['POST'])
@js_validate_payload(QUIZ_ANSWER_PAYLOAD_SCHEMA)
def post_quiz_score(quiz_key):
    attrkey_enum = current_app.extensions.get('AttrKey')
    quiz_key_enum = current_app.extensions.get('QuizKey')

    payload = request.get_json()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # make sure quiz key is valid
        try:
            quiz_id = quiz_key_enum.get_id(quiz_key)
        except ValueError:
            message = "invalid quiz_key:  %s" % quiz_key
            return message, 404

        cursor.execute('start transaction')

        # make sure the payload makes sense
        sql = """
        select word_id, attribute_id
        from quiz_candidate_v
        where quiz_key = %(QUIZ_KEY)s
        and word_id = %(WORD_ID)s
        and attribute_id = %(ATTRIBUTE_ID)s
        """
        cursor.execute(sql, {
            'QUIZ_KEY': quiz_key,
            'WORD_ID': payload['word_id'],
            'ATTRIBUTE_ID': attrkey_enum.get_id(payload['attrkey'])
        })
        rows = cursor.fetchall()
        if not rows:
            message = "payload ain't right for quiz %s" % quiz_key
            cursor.execute('rollback')
            return message, 400

        update = """
            insert into quiz_score_event
            (quiz_id, word_id, attribute_id, correct)
            VALUES
            (%(quiz_id)s, %(word_id)s, %(attribute_id)s, %(correct)s)
            """

        cursor.execute(update, {
            'quiz_id': quiz_id,
            'word_id': payload['word_id'],
            'attribute_id': attrkey_enum.get_id(payload['attrkey']),
            'correct': payload['correct']
        })
        cursor.execute('commit')

        return 'OK', 201
