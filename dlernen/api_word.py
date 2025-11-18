from flask import Blueprint, request, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js, common
from contextlib import closing
import jsonschema
import sys
import os

# view functions for /api/word URLs are here.

bp = Blueprint('api_word', __name__)


def process_word_query_result(rows):
    """
    take the rows returned by the query in get_words_from_word_ids and morph them into the format specified
    by WORDS_RESPONSE_SCHEMA.
    """
    dict_result = {}
    for r in rows:
        if not dict_result.get(r['word_id']):
            dict_result[r['word_id']] = {}
            dict_result[r['word_id']]['attributes'] = []
        attr = {
            "attrkey": r['attrkey'],
            "attrvalue": r['attrvalue'],
            "attrvalue_id": r['attrvalue_id'],
            "sort_order": r['sort_order']
        }
        dict_result[r['word_id']]['word'] = r['word']
        dict_result[r['word_id']]['word_id'] = r['word_id']
        dict_result[r['word_id']]['pos_name'] = r['pos_name']
        dict_result[r['word_id']]['attributes'].append(attr)
    result = list(dict_result.values())
    return result


def get_words_from_word_ids(word_ids):
    """
    returns word object for every valid word id.  returns empty list if no word_id was found.
    """
    format_args = ['%s'] * len(word_ids)
    format_args = ', '.join(format_args)
    sql = """
    select
        pos_name,
        word,
        word_id,
        attrkey,
        attrvalue,
        attrvalue_id,
        sort_order
    from
        mashup_v
    where word_id in (%s)
    order by sort_order
    """ % format_args

    result = []
    if word_ids:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            result = process_word_query_result(rows)

    return result


@bp.route('/api/word/<int:word_id>')
def get_word_by_id(word_id):
    """
    returns word object, or 404 if word_id not found.
    """
    word_ids = [word_id]
    words = get_words_from_word_ids(word_ids)

    jsonschema.validate(words, js.WORDS_RESPONSE_SCHEMA)

    if words:
        return words[0]

    return "word id %s not found" % word_id, 404


@bp.route('/api/word/<string:word>')
def get_word(word):
    """
    return every word that matches the given word.  will return 0 or more results, since the same word
    may appear more than once.  e.g. 'braten' is a noun and a verb.

    URL:  /api/word/<word>    optional ?partial={true|false}  -- default is false, meaning exact match.

    if partial is specified, return every word where the given word is a substring of the word OR an attribute value.
    """

    partial = request.args.get('partial', default='False').lower() == 'true'

    exact_match_sql = """
    select distinct
        word_id
    from
        mashup_v
    where word = %s
    """

    partial_match_sql = """
    select distinct
        word_id
    from
        mashup_v
    where word like %s or (attrvalue like %s and attrkey <> 'definition')
    """

    if partial:
        query = partial_match_sql
        w = "%%%s%%" % word
        query_args = (w, w)
    else:
        query = exact_match_sql
        query_args = (word,)

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(query, query_args)
        rows = cursor.fetchall()
        word_ids = list(map(lambda x: x['word_id'], rows))

        result = get_words_from_word_ids(word_ids)
        if not result:
            return "no match for %s" % word, 404

        jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

        return result


@bp.route('/api/word', methods=['POST'])
def add_word():
    """
    add a word to the dictionary.
    """
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORD_PAYLOAD_SCHEMA)

        # word isn't required in the json schema but we need it here.
        if not payload.get('word'):
            raise Exception("no word in add word request")

        # same with pos_id.
        if not payload.get('pos_id'):
            raise Exception("no part of speech in add word request")

    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    # checks:
    # - pos_id is valid
    # - attribute ids are valid for the POS
    #
    # note:  adding a word with no attributes is allowed
    #
    # jsonschema doc definitions guarantee that word contains no whitespace and that attrvalues have
    # at least one non-whitespace character.  so no checks needed for these.

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            check_sql = """
            select pos.name AS pos_name, attribute_id, pos_id 
            from pos_form 
                inner join pos on pos_id = pos.id 
                inner join attribute on attribute_id = attribute.id 
            where pos.id = %(pos_id)s
            """

            # jsonschema doc definition guarantees that payload['word']
            # will not contain whitespace.
            word = payload['word']
            pos_id = payload['pos_id']

            cursor.execute(check_sql, {'pos_id': pos_id})
            rows = cursor.fetchall()

            if not rows:
                cursor.execute('rollback')
                return "unknown part of speech:  id = %s" % payload['pos_id'], 400

            # capitalize correctly
            word = word.casefold()
            if rows[0]['pos_name'].casefold() == 'noun':
                word = word.capitalize()

            sql = "insert into word (word, pos_id) values (%s, %s)"
            cursor.execute(sql, (word, pos_id))
            cursor.execute("select last_insert_id() word_id")
            result = cursor.fetchone()
            word_id = result['word_id']

            defined_attribute_ids = {x['attribute_id'] for x in rows}
            attributes_adding = payload.get(js.ATTRIBUTES_ADDING)
            if attributes_adding:
                request_attribute_ids = {a['attribute_id'] for a in attributes_adding}
                undefined_attribute_ids = request_attribute_ids - defined_attribute_ids
                if len(undefined_attribute_ids) > 0:
                    message = "attribute ids not defined:  %s" % ', '.join(list(map(str, undefined_attribute_ids)))
                    cursor.execute('rollback')
                    return message, 400

                insert_args = [
                    {
                        "word_id": word_id,
                        "attribute_id": a['attribute_id'],
                        "attrvalue": a['attrvalue']
                    }
                    for a in attributes_adding
                ]
                if insert_args:
                    sql = """insert into word_attribute (word_id, attribute_id, attrvalue)
                    values (%(word_id)s, %(attribute_id)s, %(attrvalue)s)
                    """
                    cursor.executemany(sql, insert_args)

            cursor.execute('commit')

            return get_word_by_id(word_id)  # this is already validated and jsonified

        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "error, transaction rolled back", 500


@bp.route('/api/word/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        message = "bad payload: %s" % e.message
        return message, 400

    # checks:
    # word_id exists
    # zero-length or non-existent attribute list is ok
    # attrvalue ids exist and belong to the word, for both update and delete cases
    # attrvalue ids in deleting and updating are disjoint
    # attribute ids are defined for the word
    #
    # jsonschema doc definitions guarantee that word contains no whitespace and that attrvalues have
    # at least one non-whitespace character.  so no checks needed for these.

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = """
            select attribute_id, attrvalue_id, pos_name
            from mashup_v
            where word_id = %(word_id)s
            """
            cursor.execute(sql, {'word_id': word_id})
            rows = cursor.fetchall()
            defined_attrvalue_ids = {r['attrvalue_id'] for r in rows}
            defined_attribute_ids = {r['attribute_id'] for r in rows}
            is_noun = rows[0]['pos_name'].lower() == 'noun'

            if len(defined_attrvalue_ids) == 0:
                # word_id is bogus
                message = "word_id %s not found" % word_id
                cursor.execute('rollback')
                return message, 404

            payload_updating_attrvalue_ids = {a['attrvalue_id'] for a in payload.get('attributes_updating', set())}
            undefined_attrvalue_ids = payload_updating_attrvalue_ids - defined_attrvalue_ids
            if len(undefined_attrvalue_ids) > 0:
                message = "attrvalue_ids not defined:  %s" % ', '.join(list(undefined_attrvalue_ids))
                cursor.execute('rollback')
                return message, 400

            payload_deleting_attrvalue_ids = set(payload.get('attributes_deleting', []))
            undefined_attrvalue_ids = payload_deleting_attrvalue_ids - defined_attrvalue_ids
            if len(undefined_attrvalue_ids) > 0:
                message = "attrvalue_ids not defined:  %s" % ', '.join(list(undefined_attrvalue_ids))
                cursor.execute('rollback')
                return message, 400

            deleting_and_updating_ids = payload_deleting_attrvalue_ids & payload_updating_attrvalue_ids
            if deleting_and_updating_ids:
                message = "attempting to delete and update attr ids:  %s" % ', '.join(list(deleting_and_updating_ids))
                cursor.execute('rollback')
                return message, 400

            payload_updating_attrvalue_ids = {a['attrvalue_id'] for a in payload.get('attributes_updating', set())}
            undefined_attrvalue_ids = payload_updating_attrvalue_ids - defined_attrvalue_ids
            if len(undefined_attrvalue_ids) > 0:
                message = "attrvalue_ids not defined:  %s" % ', '.join(list(undefined_attrvalue_ids))
                cursor.execute('rollback')
                return message, 400

            payload_adding_attribute_ids = {a['attribute_id'] for a in payload.get(js.ATTRIBUTES_ADDING, set())}
            undefined_attribute_ids = payload_adding_attribute_ids - defined_attribute_ids
            if len(undefined_attribute_ids) > 0:
                message = "attrids not defined:  %s" % ', '.join(list(undefined_attribute_ids))
                cursor.execute('rollback')
                return message, 400

            # jsonschema definition guarantees that word, if present, will not contain whitespace
            word = payload.get('word', '')

            # capitalize appropriately.
            word = word.casefold()
            if is_noun:
                word = word.capitalize()

            # checks complete, let's do this.

            if word:
                sql = """
                update word set word = %(word)s
                where id = %(word_id)s
                """
                d = {
                    'word': word,
                    'word_id': word_id
                }
                cursor.execute(sql, d)

            sql = """
            update word_attribute
            set attrvalue = %(attrvalue)s
            where id = %(attrvalue_id)s
            """
            update_args = [
                {
                    'attrvalue': a['attrvalue'].strip(),
                    'attrvalue_id': a['attrvalue_id']
                }
                for a in payload.get('attributes_updating', set())
            ]
            if update_args:
                cursor.executemany(sql, update_args)

            sql = """
            insert ignore into word_attribute(attribute_id, word_id, attrvalue)
            values (%(attribute_id)s, %(word_id)s, %(attrvalue)s)
            """
            insert_args = [
                {
                    'attrvalue': a['attrvalue'].strip(),
                    'word_id': word_id,
                    'attribute_id': a['attribute_id']
                }
                for a in payload.get(js.ATTRIBUTES_ADDING, set())
            ]
            if insert_args:
                cursor.executemany(sql, insert_args)

            sql = """
            delete from word_attribute where id = %s
            """
            if payload_deleting_attrvalue_ids:
                # args to executemany have to be a 2d list, i.e. list of lists
                args = [[x] for x in payload_deleting_attrvalue_ids]
                cursor.executemany(sql, args)

            cursor.execute('commit')

            return get_word_by_id(word_id)

        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "error, transaction rolled back", 500


@bp.route('/api/word/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            sql = """
            delete from word
            where id = %(word_id)s
            """
            cursor.execute(sql, {'word_id': word_id})
            cursor.execute('commit')
            return 'OK'
        except Exception as e:
            cursor.execute('rollback')
            return 'error deleting word_id %s' % word_id, 500


@bp.route('/api/words', methods=['GET'])
def get_words_in_wordlists():
    """
    given a list of wordlist ids, get all the words in those lists.  if no word list ids are given, dump
    the whole dictionary.
    """
    # TODO - currently no unit tests for this.  do we need any?

    wordlist_ids = request.args.get('wordlist_id')  # this will come in as a comma-separated string.
    if wordlist_ids:
        wordlist_ids = wordlist_ids.split(',')
        wordlist_ids = list(set(wordlist_ids))

        word_ids = common.get_word_ids_from_wordlists(wordlist_ids)
    else:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = """
            select id as word_id from word
            """

            cursor.execute(sql)
            rows = cursor.fetchall()

            word_ids = list(map(lambda x: x['word_id'], rows))

    result = get_words_from_word_ids(word_ids)

    jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

    return result


@bp.route('/api/words', methods=['PUT'])
def get_words():
    # this is for PUT requests because we have to send in the list of words ids as a payload.
    # if we try to put the word_ids into a GET URL, the URL might be too long.
    """
    given a list of word_ids, get the details for each word:  word, attributes, etc.
    """

    payload = request.get_json()

    word_ids = payload.get('word_ids', [])
    result = get_words_from_word_ids(word_ids)

    jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

    return result
