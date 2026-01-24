from flask import Blueprint, request, current_app, url_for
import requests
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js, common
from contextlib import closing
import jsonschema

# view functions for /api/word URLs are here.

bp = Blueprint('api_word', __name__, url_prefix='/api/word')


@bp.route('/<int:word_id>')
def get_word_by_id(word_id):
    """
    returns word object, or 404 if word_id not found.
    """
    word_ids = [word_id]
    words = common.get_words_from_word_ids(word_ids)

    jsonschema.validate(words, js.WORDS_RESPONSE_SCHEMA)

    if words:
        return words[0]

    return "word id %s not found" % word_id, 404


@bp.route('/<string:word>')
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

        result = common.get_words_from_word_ids(word_ids)
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


@bp.route('', methods=['POST'])
def add_word():
    # add a single word to the dictionary.  the word's part-of-speech must be specified.  if successful, this
    # operation creates a single word id.

    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORD_ADD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    # word and pos_id are required fields in the json schema.  so if the payload passes validation we know these
    # are present.

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
    if not r:
        return r.text, r.status_code

    pos_structures = r.json()
    pos_structure = list(filter(lambda x: x['pos_id'] == pos_id, pos_structures))
    if not pos_structure:
        # pos_id is bogus
        message = "unknown part of speech:  %s" % pos_id
        return message, 404

    # pos_structure is a length-1 array, get the first element
    pos_structure = pos_structure[0]

    # capitalize correctly.  use lower() and not casefold() because casefold() can change what we type:
    # ß will become ss for example.
    word = word.lower()
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

            # adding a new word should refresh all wordlists where the word is previously unknown.

            sql = """
            select wordlist_id
            from wordlist_unknown_word
            where word = %(word)s
            """
            cursor.execute(sql, {'word': word})
            wordlist_ids = cursor.fetchall()

            insert_args = [(r['wordlist_id'], word_id) for r in wordlist_ids]
            if insert_args:
                sql = """
                insert ignore
                into wordlist_known_word (wordlist_id, word_id)
                values (%s, %s)
                """

                cursor.executemany(sql, insert_args)

            sql = """
            delete from wordlist_unknown_word
            where word = %(word)s
            """
            cursor.execute(sql, {'word': payload['word']})

            cursor.execute('commit')

            return get_word_by_id(word_id), 201  # this is already validated and jsonified

        except Exception as e:
            cursor.execute('rollback')
            return "error, transaction rolled back", 500


@bp.route('/<int:word_id>', methods=['PUT'])
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
    if not r:
        return r.text, r.status_code

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

    # use lower() here, not casefold().  casefold() changes 'ß' to 'ss'.  so if we change the spelling
    # of a word by changing ss to ß, nothing will happen.
    word = word.lower()
    if is_noun:
        word = word.capitalize()  # this will not change ß to ss

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
            cursor.execute('rollback')
            return "error, transaction rolled back", 500


@bp.route('/<int:word_id>', methods=['DELETE'])
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
