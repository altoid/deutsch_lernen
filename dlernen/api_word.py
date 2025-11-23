from flask import Blueprint, request, current_app, url_for
import requests
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


def save_attributes(word_id, attributes_adding, attributes_deleting, cursor):
    if attributes_adding:
        args = [
            {
                "word_id": word_id,
                "attribute_id": a['attribute_id'],
                "attrvalue": a['attrvalue']
            }
            for a in attributes_adding
        ]

        sql = """
        insert into word_attribute (word_id, attribute_id, attrvalue)
        values (%(word_id)s, %(attribute_id)s, %(attrvalue)s)
        on duplicate key update attrvalue=%(attrvalue)s
        """
        cursor.executemany(sql, args)

    if attributes_deleting:
        sql = """
        delete from word_attribute 
        where word_id = %(word_id)s and attribute_id = %(attribute_id)s
        """

        args = [
            {
                'word_id': word_id,
                'attribute_id': a['attribute_id']
            }
            for a in attributes_deleting
        ]

        cursor.executemany(sql, args)


@bp.route('/api/word', methods=['POST'])
def add_word():
    """
    add a word to the dictionary.
    """
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORD_ADD_PAYLOAD_SCHEMA)

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

    # jsonschema doc definition guarantees that payload['word']
    # will not contain whitespace.
    word = payload['word']
    pos_id = payload['pos_id']

    # checks:
    # - pos_id is valid
    # - attribute ids are valid for the POS
    # - attribute ids are unique; we don't provide multiple values for the same attribute
    #
    # note:  adding a word with no attributes is allowed
    #
    # jsonschema doc definitions guarantee that word contains no whitespace and that attrvalues have
    # at least one non-whitespace character.  so no checks needed for these.

    url = url_for('api_pos.get_pos', _external=True)
    r = requests.get(url)
    pos_structures = r.json()
    pos_structure = list(filter(lambda x: x['pos_id'] == pos_id, pos_structures))
    if not pos_structure:
        # pos_id is bogus
        message = "unknown part of speech:  %s" % pos_id
        return message, 404

    # pos_structure is a length-1 array, get the first element
    pos_structure = pos_structure[0]

    # capitalize correctly
    word = word.casefold()
    if pos_structure['pos_name'].casefold() == 'noun':
        word = word.capitalize()

    defined_attribute_ids = {x['attribute_id'] for x in pos_structure['attributes']}
    attr_ids_to_keys = {x['attribute_id']: x['attrkey'] for x in pos_structure['attributes']}
    attributes = payload.get(js.ATTRIBUTES)
    attributes_adding = None
    if attributes:
        request_attribute_ids = {a['attribute_id'] for a in attributes}
        undefined_attribute_ids = request_attribute_ids - defined_attribute_ids
        if len(undefined_attribute_ids) > 0:
            message = "attribute ids not defined:  %s" % ', '.join(list(map(str, undefined_attribute_ids)))
            return message, 400

        request_attribute_ids_list = [a['attribute_id'] for a in attributes]
        if len(request_attribute_ids_list) != len(request_attribute_ids):
            message = "multiple values provided for the same attribute", 400
            return message, 400

        attributes_adding = []
        for a in attributes:
            if 'attrvalue' in a:
                attributes_adding.append(a)

        for a in attributes_adding:
            if attr_ids_to_keys[a['attribute_id']].casefold() == 'plural':
                a['attrvalue'] = a['attrvalue'].capitalize()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = "insert into word (word, pos_id) values (%s, %s)"
            cursor.execute(sql, (word, pos_id))
            cursor.execute("select last_insert_id() word_id")
            result = cursor.fetchone()
            word_id = result['word_id']

            save_attributes(word_id, attributes_adding, None, cursor)

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
        jsonschema.validate(payload, js.WORD_UPDATE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        message = "bad payload: %s" % e.message
        return message, 400

    # checks:
    # word_id exists
    # attrvalue ids exist and belong to the word
    # attribute ids are defined for the word
    # attribute ids being written/deleted are disjoint.
    # we aren't trying to write more than one value for the same attribute
    #
    # jsonschema doc definitions guarantee that word contains no whitespace and that attrvalues have
    # at least one non-whitespace character.  so no checks needed for these.

    url = url_for('api_pos.get_pos_for_word_id', word_id=word_id, _external=True)
    r = requests.get(url)
    pos_structure = r.json()
    if not pos_structure:
        # word_id is bogus
        message = "word_id %s not found" % word_id
        return message, 404

    # pos_structure is a length-1 array, get the first element
    pos_structure = pos_structure[0]

    defined_attribute_ids = {a['attribute_id'] for a in pos_structure['attributes']}

    given_attribute_ids = {a['attribute_id'] for a in payload.get(js.ATTRIBUTES, set())}
    undefined_attribute_ids = given_attribute_ids - defined_attribute_ids
    if len(undefined_attribute_ids) > 0:
        ids = list(map(str, undefined_attribute_ids))
        message = "attribute_ids not defined:  %s" % ', '.join(ids)
        return message, 400

    attributes = payload.get(js.ATTRIBUTES, [])
    attributes_adding = []
    attributes_deleting = []
    for a in attributes:
        if 'attrvalue' in a:
            attributes_adding.append(a)
        else:
            attributes_deleting.append(a)

    attrids_adding_list = [x['attribute_id'] for x in attributes_adding]
    attrids_adding_set = set(attrids_adding_list)
    if len(attrids_adding_set) != len(attrids_adding_list):
        return "attempting to write multiple values for an attribute", 400

    attrids_deleting_set = {x['attribute_id'] for x in attributes_deleting}

    deleting_and_updating_ids = attrids_deleting_set & attrids_adding_set
    if deleting_and_updating_ids:
        ids = list(map(str, deleting_and_updating_ids))
        message = "attempting to delete and update attr ids:  %s" % ', '.join(ids)
        return message, 400

    # checks complete, let's do this.

    word = payload.get('word', '')

    # capitalize appropriately.
    is_noun = pos_structure['pos_name'].casefold() == 'noun'
    word = word.casefold()
    if is_noun:
        word = word.capitalize()

    # noun plurals must be capitalized.
    attr_ids_to_keys = {a['attribute_id']: a['attrkey'] for a in pos_structure['attributes']}
    for a in attributes_adding:
        if attr_ids_to_keys[a['attribute_id']].casefold() == 'plural':
            a['attrvalue'] = a['attrvalue'].capitalize()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

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

            save_attributes(word_id, attributes_adding, attributes_deleting, cursor)

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
