from flask import Flask, request, render_template, redirect, url_for
from pprint import pprint
from mysql.connector import connect
from dlernen.config import Config
from dlernen import quiz_sql
import requests
import json
from contextlib import closing
import dlernen.dlernen_json_schema
import jsonschema
import sys
import os

app = Flask(__name__)
app.config.from_object(Config)


# TODO strip strings before storing in DB


def chunkify(arr, **kwargs):
    if not arr:
        return []

    nchunks = kwargs.get('nchunks')
    chunksize = kwargs.get('chunksize')
    if not nchunks and not chunksize:
        # return the whole array as one chunk
        return [arr]

    if nchunks and chunksize:
        raise Exception('set chunksize or nchunks but not both')

    arraysize = len(arr)
    if nchunks:
        # round up array size to nearest multiple of nchunks
        arraysize = ((arraysize + nchunks - 1) // nchunks) * nchunks
        chunksize = arraysize // nchunks

    # add one more increment of chunksize so that our zip array includes
    # the last elements
    chunks = [x for x in range(0, arraysize + chunksize, chunksize)]

    z = list(zip(chunks, chunks[1:]))

    result = []
    for x in z:
        result.append(arr[x[0]:x[1]])
    return result


@app.route('/api/post_test', methods=['POST'])
def post_test():
    """
    apparently you can't use requests to send true JSON objects in a post request.  i.e. this did not work:

    IDS = [1, 2, 3, 4, 5]
    DATA = {
        "key": "value",
        "arr": IDS,     <== this is valid json but only the first item in the array is sent.
        "a": "aoeu"
    }

    but this did:

    IDS = [1, 2, 3, 4, 5]
    DATA = {
        "key": "value",
        "arr": json.dumps(IDS),  <== have to stringify the array before sending it over.
        "a": "aoeu"
    }
    """

    j = request.get_json()
    pprint(j)
    return j


def get_word_ids_for_attrkey(limit, recent, attrkey):
    query = """
        select word_id
        from mashup_v m
        where attrkey = %(attrkey)s
        and attrvalue is not null 
        """
    if recent:
        order_by = "order by m.added desc "
    else:
        order_by = "order by rand() "
    query += order_by
    limit_clause = "limit %(limit)s " if limit else ""
    query += limit_clause
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        args = {
            "limit": limit,
            "attrkey": attrkey
        }
        cursor.execute(query, args)
        query_result = cursor.fetchall()
        return [x['word_id'] for x in query_result]


def get_word_ids_from_list_ids(limit, wordlist_ids, recent, attrkey):
    """
    returns a list containing 0 or more unique word ids.
    """

    results = []
    wordlist_ids = wordlist_ids.split(',')

    for wordlist_id in wordlist_ids:
        # use the API so we don't have to worry about whether any are smart lists
        url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
        r = requests.get(url)
        result = json.loads(r.text)
        if result:
            results.append(result)

    # dig the word_ids out of the list results
    word_ids = []
    for result in results:
        word_ids += [x['word_id'] for x in result.get('known_words')]

    word_ids = list(set(word_ids))

    # we'll have to apply the recent and limit filters here in software
    if len(word_ids):
        query = """
            select word_id
            from mashup_v
            where attrkey = %%s
            and attrvalue is not null
            and word_id in (%s)
            """ % (','.join(['%s'] * len(word_ids)))

        if recent:
            order_by = " order by mashup_v.added desc "
        else:
            order_by = " order by rand() "

        query += order_by

        limit_clause = " limit %s "

        query += limit_clause

        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            args = [attrkey] + word_ids + [limit]
            cursor.execute(query, args)

            query_result = cursor.fetchall()

            word_ids = [x['word_id'] for x in query_result]

    return word_ids


@app.route('/api/words/<string:attrkey>')
def words_attrkey(attrkey):
    """
    request format is

    recent={true|false} - optional, default is false
    if true, select the word ids by added date, most recent first
    if false or not specified, selects by rand()

    limit=n - optional.  restrict the number of word ids.  defaults to 10 if not specified.

    wordlist_id=n,n,n - optional.  restrict the word ids to those in the given lists.

    returns a list of all of the word_ids that match the constraints.
    the ids are unique but the order is undefined.
    """

    # check that the attrkey exists
    sql = """
    select attrkey from attribute
    """
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(sql)
        query_result = cursor.fetchall()
        keys = {x['attrkey'] for x in query_result}
        if attrkey not in keys:
            return "attrkey %s not found" % attrkey, 404

        recent = request.args.get('recent', default='False').lower() == 'true'
        try:
            limit = int(request.args.get('limit', default='10'))
            if limit < 1:
                return "bad value for limit", 400
        except ValueError as dammit:
            return "bad value for limit", 400

        wordlist_ids = request.args.get('wordlist_id')
        if wordlist_ids:
            word_ids = get_word_ids_from_list_ids(limit, wordlist_ids, recent, attrkey)
        else:
            word_ids = get_word_ids_for_attrkey(limit, recent, attrkey)

        result = {
            "word_ids": word_ids
        }

        jsonschema.validate(result, dlernen.dlernen_json_schema.WORDIDS_SCHEMA)

        return result


@app.route('/api/quiz_data', methods=['PUT', 'POST'])
def quiz_data():
    """
    given a quiz key and a list of word_ids, get all of the attribute values quizzed for each of the words.

    although this is invoked with a PUT request, this doesn't actually change the state of the server.  we
    use PUT so that we can have longer list of word ids than we can put into a GET url, so the request is idempotent.
    """
    if request.method == 'PUT':
        payload = request.get_json()

        quizkey = payload['quizkey']
        word_ids = payload.get('word_ids', [])
        word_ids = list(map(str, word_ids))
        word_ids = ','.join(word_ids)
        result = []
        if word_ids:
            query = quiz_sql.build_quiz_query(quizkey, word_ids)
            with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                results_dict = {}

                for row in rows:
                    keez = row.keys()
                    if row['word_id'] not in results_dict:
                        results_dict[row['word_id']] = {
                            k: row.get(k) for k in keez & {
                                'qname',
                                'quiz_id',
                                'word_id',
                                'word'
                            }
                        }
                    if row['attrkey'] not in results_dict[row['word_id']]:
                        results_dict[row['word_id']][row['attrkey']] = {
                            k: row.get(k) for k in keez & {
                                'correct_count',
                                'presentation_count',
                                'attrvalue',
                                'attribute_id',
                                'last_presentation'
                            }
                        }
                result = list(results_dict.values())

        return result

    update = """
        insert into quiz_score
        (quiz_id, word_id, attribute_id, presentation_count, correct_count)
        VALUES
        (%(quiz_id)s, %(word_id)s, %(attribute_id)s, %(presentation_count)s, %(correct_count)s)
        on duplicate key update
        presentation_count = values(presentation_count),
        correct_count = values(correct_count)
        """

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(update, request.form)
        dbh.commit()

    return 'OK'


def process_word_query_result(rows):
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
        pf.sort_order
    from
        mashup_v
    inner join pos_form pf on pf.attribute_id = mashup_v.attribute_id and pf.pos_id = mashup_v.pos_id
    where word_id in
        (
        select
            word_id
        from
            mashup_v
        where
            word_id in (%s)
        )
    """ % format_args

    result = []
    if word_ids:
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            cursor.execute(sql, word_ids)
            rows = cursor.fetchall()
            result = process_word_query_result(rows)

    return result


@app.route('/api/word/<int:word_id>')
def get_word_by_id(word_id):
    """
    returns word object, or 404 if word_id not found.
    """
    word_ids = [word_id]
    words = get_words_from_word_ids(word_ids)

    jsonschema.validate(words, dlernen.dlernen_json_schema.WORDS_SCHEMA)

    if words:
        return words[0]

    return "word id %s not found" % word_id, 404


@app.route('/api/word/<string:word>')
def get_word(word):
    """
    return attributes for every word that matches <word>.  since
    words are not unique (e.g. Bank), it is possible to return more than
    one set of attributes for a given word.  ex: 'braten' is a noun
    and a verb.

    URL:  /api/word/<word>    optioral ?partial={true|false}  -- default is false, meaning exact match.

    :param word:
    :return:

    """

    partial = request.args.get('partial', default='False').lower() == 'true'

    exact_match_sql = """
select
    pos_name,
    word,
    word_id,
    attrkey,
    attrvalue,
    attrvalue_id,
    pf.sort_order
from
    mashup_v
inner join pos_form pf on pf.attribute_id = mashup_v.attribute_id and pf.pos_id = mashup_v.pos_id
where word = %s
order by word_id, pf.sort_order
"""

    partial_match_sql = """
    select
        pos_name,
        word,
        word_id,
        attrkey,
        attrvalue,
        attrvalue_id,
        pf.sort_order
    from
        mashup_v
    inner join pos_form pf on pf.attribute_id = mashup_v.attribute_id and pf.pos_id = mashup_v.pos_id
    where word like %s or attrvalue like %s
    order by word_id, pf.sort_order
    """

    if partial:
        query = partial_match_sql
        w = "%%%s%%" % word
        query_args = (w, w)
    else:
        query = exact_match_sql
        query_args = (word,)

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(query, query_args)
        rows = cursor.fetchall()
        result = process_word_query_result(rows)
        if not result:
            return "no match for %s" % word, 404

        jsonschema.validate(result, dlernen.dlernen_json_schema.WORDS_SCHEMA)

        return result


@app.route('/api/word', methods=['POST'])
def add_word():
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # checks:
    # - pos_name is valid
    # - word is valid (nonempty when stripped)
    # - attrkeys are valid for the POS
    # - attrvalues are not degenerate
    # note:  adding a word with no attributes is allowed

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            check_sql = """
            select distinct attrkey, attribute_id, pos_id
            from mashup_v
            where pos_name = %(pos_name)s
            """

            pos_name = payload['pos_name'].strip()
            word = payload['word'].strip()
            if not word:
                return "word cannot be empty string", 400

            d = {
                'pos_name': pos_name
            }

            cursor.execute(check_sql, d)
            rows = cursor.fetchall()

            # maps attr keys to attr ids
            attrdict = {r['attrkey']: r['attribute_id'] for r in rows}

            if len(attrdict) == 0:
                cursor.execute('rollback')
                return "unknown part of speech:  %s" % payload['pos_name'], 400

            pos_id = rows[0]['pos_id']
            defined_attrkeys = set(attrdict.keys())

            request_attrkeys = {a['attrkey'].strip() for a in payload.get('attributes', set())}
            undefined_attrkeys = request_attrkeys - defined_attrkeys
            if len(undefined_attrkeys) > 0:
                message = "attribute keys not defined:  %s" % ', '.join(list(undefined_attrkeys))
                cursor.execute('rollback')
                return message, 400

            # check that attrvalues are all strings len > 0
            payload_attrvalues = {a['attrvalue'].strip() for a in payload.get('attributes', set())}
            bad_attrvalues = list(filter(lambda x: not bool(x), payload_attrvalues))
            if len(bad_attrvalues) > 0:
                message = "attribute values cannot be empty strings"
                cursor.execute('rollback')
                return message, 400

            sql = "insert into word (word, pos_id) values (%s, %s)"
            cursor.execute(sql, (word, pos_id))
            cursor.execute("select last_insert_id() word_id")
            result = cursor.fetchone()
            word_id = result['word_id']

            insert_args = [
                {
                    "word_id": word_id,
                    "attribute_id": attrdict[a['attrkey']],
                    "attrvalue": a['attrvalue'].strip()
                }
                for a in payload.get('attributes', set())
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


@app.route('/api/word/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # checks:
    # word_id exists
    # word is nonempty if present
    # zero-length or non-existent attribute list is ok
    # attrvalue ids exist and belong to the word, for both update and delete cases
    # attrvalue ids in deleting and updating are disjoint
    # attrkeys are defined for the word, for both update and add cases
    # new attrvalues are all strings len > 0.

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = """
            select attrkey, attribute_id, attrvalue_id
            from mashup_v
            where word_id = %(word_id)s
            """
            cursor.execute(sql, {'word_id': word_id})
            rows = cursor.fetchall()
            defined_attrvalue_ids = {r['attrvalue_id'] for r in rows}
            defined_attrkeys = {r['attrkey'] for r in rows}

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

            payload_adding_attrkeys = {a['attrkey'] for a in payload.get('attributes_adding', set())}
            undefined_attrkeys = payload_adding_attrkeys - defined_attrkeys
            if len(undefined_attrkeys) > 0:
                message = "attrkeys not defined:  %s" % ', '.join(list(undefined_attrkeys))
                cursor.execute('rollback')
                return message, 400

            word = None
            if 'word' in payload:
                word = payload['word'].strip()
            if word == '':
                message = 'word cannot be empty string'
                return message, 400

            # check that attrvalues are all strings len > 0
            payload_attrvalues = {a['attrvalue'].strip() for a in payload.get('attributes', set())}
            bad_attrvalues = list(filter(lambda x: not bool(x), payload_attrvalues))
            if len(bad_attrvalues) > 0:
                message = "attribute values cannot be empty strings"
                cursor.execute('rollback')
                return message, 400

            # checks complete, let's do this.
            attrdict = {r['attrkey']: r['attribute_id'] for r in rows}

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
                    'attribute_id': attrdict[a['attrkey']]
                }
                for a in payload.get('attributes_adding', set())
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


@app.route('/api/word/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
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


@app.route('/api/words', methods=['PUT'])
def get_words():
    # this is for PUT requests because we have to send in the list of words ids as a payload.
    # if we try to put the word_ids into a GET URL, the URL might be too long.
    """
    given a list of word_ids, get the details for each word:  word, attributes, etc.
    """

    payload = request.get_json()

    word_ids = payload.get('word_ids', [])
    result = get_words_from_word_ids(word_ids)

    jsonschema.validate(result, dlernen.dlernen_json_schema.WORDS_SCHEMA)

    return result


# TODO - delete an attribute value - /api/<word_id>/attribute/<attrvalue_id>


@app.route('/api/<int:word_id>/attribute', methods=['POST'])
def add_attributes(word_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        pprint(e)
        return "bad payload: %s" % e.message, 400

    # checks:
    # word_id exists
    # zero-length attribute list is ok
    # attrvalue ids exist and belong to the word
    # new attrvalues are all strings len > 0.

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = """
            select attrkey, attribute_id
            from mashup_v where word_id = %(word_id)s
            """
            cursor.execute(sql, {'word_id': word_id})
            rows = cursor.fetchall()
            if len(rows) == 0:
                cursor.execute('rollback')
                return "no such word id:  %s" % word_id, 400

            defined_attrkeys = {r['attrkey'] for r in rows}
            payload_attrkeys = {a['attrkey'].strip() for a in payload['attributes']}

            undefined_attrkeys = payload_attrkeys - defined_attrkeys
            if len(undefined_attrkeys) > 0:
                wtf = ', '.join(undefined_attrkeys)
                message = "invalid attrkeys:  %s" % wtf
                cursor.execute('rollback')
                return message, 400

            payload_attrvalues = [a['attrvalue'].strip() for a in payload['attributes']]
            bad_attrvalues = list(filter(lambda x: not bool(x), payload_attrvalues))
            if len(bad_attrvalues) > 0:
                message = "attribute values cannot be empty strings"
                cursor.execute('rollback')
                return message, 400

            # checks complete, let's do this
            rows_to_insert = []
            attrdict = {r['attrkey']: r['attribute_id'] for r in rows}
            for a in payload['attributes']:
                t = (attrdict[a['attrkey']], word_id, a['attrvalue'].strip())
                rows_to_insert.append(t)

            if rows_to_insert:
                # pprint(rows_to_insert)
                sql = """
                insert into word_attribute (attribute_id, word_id, attrvalue)
                values (%s, %s, %s)
                """
                cursor.executemany(sql, rows_to_insert)

            cursor.execute('commit')

            return get_word_by_id(word_id)  # this is already validated and jsonified

        except Exception as e:
            pprint(e)
            cursor.execute('rollback')
            return 'error adding attributes to word_id %s' % word_id, 500


@app.route('/api/gender_rules')
def gender_rules():
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        query = """
        select article, rule
        from gender_rule
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


@app.route('/api/wordlist/<int:wordlist_id>/metadata')
def get_list_attributes(wordlist_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
    select
        id wordlist_id, name, ifnull(citation, '') citation, ifnull(sqlcode, '') sqlcode
     from wordlist
    where id = %s
    """
        cursor.execute(sql, (wordlist_id,))
        wl_row = cursor.fetchone()

        jsonschema.validate(wl_row, dlernen.dlernen_json_schema.WORDLIST_METADATA_SCHEMA)

        return wl_row


@app.route('/api/wordlist/<int:wordlist_id>')
def get_wordlist(wordlist_id):
    # uses WORDLIST_SCHEMA
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            id wordlist_id,
            name,
            ifnull(citation, '') citation,
            ifnull(notes, '') notes,
            ifnull(sqlcode, '') sqlcode
        from wordlist
        where id = %s
        """
        cursor.execute(sql, (wordlist_id,))
        wl_row = cursor.fetchone()
        if not wl_row:
            return "wordlist %s not found" % wordlist_id, 404

        sqlcode = wl_row['sqlcode'].strip()

        result = dict(wl_row)
        result['source_is_url'] = result['citation'].startswith('http') if result['citation'] else False

        if sqlcode:
            known_words_sql = """
            with matching as ( %s )
            select
                  m.word word,
                  matching.word_id,
                  m.attrvalue definition,
                  m2.attrvalue article  -- possibly null
            from  matching
            left  join mashup_v m
            on    matching.word_id = m.word_id
            and   m.attrkey = 'definition'
            left  join mashup_v m2
            on    matching.word_id = m2.word_id
            and   m2.attrkey = 'article'
            order by m.word        
            """ % sqlcode

            cursor.execute(known_words_sql)

        else:
            known_words_sql = """
            select
                m.word,
                m.word_id,
                m.attrvalue definition,
                m2.attrvalue article  -- possibly null
            from wordlist_known_word ww
            left join mashup_v m
            on   ww.word_id = m.word_id
            and  m.attrkey = 'definition'
            left join mashup_v m2
            on   ww.word_id = m2.word_id
            and  m2.attrkey = 'article'
            where ww.wordlist_id = %s
            order by m.word
            """

            cursor.execute(known_words_sql, (wordlist_id,))

        known_words = cursor.fetchall()

        result['known_words'] = known_words

        unknown_words_sql = """
        select
        ww.word word
        from wordlist_unknown_word ww
        where ww.wordlist_id = %s
        order by ww.word
        """

        cursor.execute(unknown_words_sql, (wordlist_id,))
        unknown_words = cursor.fetchall()
        unknown_words = [x['word'] for x in unknown_words]

        result['unknown_words'] = unknown_words

        if sqlcode:
            result['list_type'] = "smart"
        elif unknown_words or known_words:
            result['list_type'] = "standard"
        else:
            result['list_type'] = "empty"

        jsonschema.validate(result, dlernen.dlernen_json_schema.WORDLIST_SCHEMA)

        return result


def add_words_to_list(cursor, wordlist_id, words):
    arglist = list(words)
    format_list = ['%s'] * len(arglist)
    format_list = ', '.join(format_list)

    sql = """
    select distinct id word_id, word
    from word
    where word in (%s)
    """ % format_list

    cursor.execute(sql, arglist)
    rows = cursor.fetchall()
    known_words = {x['word'] for x in rows}
    unknown_words = words - known_words
    wkw_tuples = [(wordlist_id, r['word_id']) for r in rows]
    if wkw_tuples:
        ins_sql = """
        insert ignore into wordlist_known_word (wordlist_id, word_id)
        values (%s, %s)
        """
        cursor.executemany(ins_sql, wkw_tuples)

    if unknown_words:
        ins_sql = """
        insert ignore into wordlist_unknown_word (wordlist_id, word)
        values (%s, %s)
        """
        wuw_tuples = [(wordlist_id, x) for x in unknown_words]
        cursor.executemany(ins_sql, wuw_tuples)


@app.route('/api/wordlist', methods=['POST'])
def add_wordlist():
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    name = payload.get('name')
    citation = payload.get('citation')
    sqlcode = payload.get('sqlcode')
    notes = payload.get('notes')
    words = payload.get('words')

    if sqlcode is not None:
        sqlcode = sqlcode.strip()
    if name is not None:
        name = name.strip()
    if citation is not None:
        citation = citation.strip()
    if words is not None:
        words = [w.strip() for w in words]
        words = set(filter(lambda x: bool(x), words))

    if not name:
        return "can't create list with empty name", 400

    if sqlcode and words:
        return "can't create list with sqlcode and words", 400

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # this is well-behaved if citation and sqlcode are not given.

        try:
            cursor.execute('start transaction')
            sql = "insert into wordlist (`name`, `citation`, `sqlcode`, `notes`) values (%s, %s, %s, %s)"
            cursor.execute(sql, (name, citation, sqlcode, notes))
            cursor.execute("select last_insert_id() wordlist_id")
            result = cursor.fetchone()
            wordlist_id = result['wordlist_id']

            # figure out which words are known and not known
            if words:
                add_words_to_list(cursor, wordlist_id, words)

            cursor.execute('commit')

            return get_wordlist(wordlist_id)
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "create list failed", 500


@app.route('/api/wordlist/<int:wordlist_id>', methods=['DELETE'])
def delete_wordlist(wordlist_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "delete from wordlist where id = %s"
            cursor.execute(sql, (wordlist_id,))
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:wordlist_id>/<int:word_id>', methods=['DELETE'])
def delete_from_wordlist_by_id(wordlist_id, word_id):
    # removes from known words only
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "select sqlcode from wordlist where id = %s"
            cursor.execute(sql, (wordlist_id,))
            row = cursor.fetchone()
            if row and row['sqlcode']:
                cursor.execute('rollback')
                return "can't delete words from smart list", 400
            sql = "delete from wordlist_known_word where wordlist_id = %s and word_id = %s"
            cursor.execute(sql, (wordlist_id, word_id))
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:wordlist_id>/<string:word>', methods=['DELETE'])
def delete_from_wordlist_by_word(wordlist_id, word):
    # removes from unknown words only
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            word = word.strip()
            if word:
                cursor.execute('start transaction')
                sql = "select sqlcode from wordlist where id = %s"
                cursor.execute(sql, (wordlist_id,))
                row = cursor.fetchone()
                if row and row['sqlcode']:
                    cursor.execute('rollback')
                    return "can't delete words from smart list", 400
                sql = "delete from wordlist_unknown_word where wordlist_id = %s and word = %s"
                cursor.execute(sql, (wordlist_id, word))
                cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:wordlist_id>', methods=['PUT'])
def update_wordlist(wordlist_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # don't update anything that isn't in the payload.
    update_args = {}
    sqlcode = words = None
    if 'name' in payload:
        name = payload.get('name')
        if name is not None:
            name = name.strip()
        update_args['name'] = name

    if 'citation' in payload:
        citation = payload.get('citation')
        if citation is not None:
            citation = citation.strip()
        update_args['citation'] = citation

    if 'sqlcode' in payload:
        sqlcode = payload.get('sqlcode')
        if sqlcode is not None:
            sqlcode = sqlcode.strip()
        update_args['sqlcode'] = sqlcode

    if 'notes' in payload:
        notes = payload.get('notes')
        update_args['notes'] = notes

    if 'words' in payload:
        words = payload.get('words')
        if words is not None:
            words = [w.strip() for w in words]
            # get the words that are not empty strings or None
            words = set(filter(lambda x: bool(x), words))

    if sqlcode and words:
        return "can't modify list with sqlcode and words", 400

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # this is well-behaved if citation and sqlcode are not given.
        cursor.execute('start transaction')

        existing_list = get_wordlist(wordlist_id)
        if existing_list['list_type'] == 'smart' and words and sqlcode != '':
            # if sqlcode is the empty string, then this is ok, because it means we are going to
            # clear out the existing sqlcode.
            cursor.execute('rollback')
            return "can't add words to smart list", 400

        if existing_list['list_type'] == 'standard' and sqlcode:
            cursor.execute('rollback')
            return "can't add code to existing list", 400

        try:
            cursor.execute('start transaction')
            if update_args:
                update_args['wordlist_id'] = wordlist_id

                keez = ['name', 'notes', 'citation', 'sqlcode']
                clauses = []
                for k in keez:
                    if k in update_args:
                        clauses.append('`%(key)s` = %%(%(key)s)s' % {'key': k})

                sql = """
                update wordlist
                set %(clauses)s
                where id = %%(wordlist_id)s
                """ % {'clauses': ', '.join(clauses)}

                # print(sql)
                # pprint(update_args)
                cursor.execute(sql, update_args)

            if words:
                add_words_to_list(cursor, wordlist_id, words)

            cursor.execute('commit')

            return get_wordlist(wordlist_id)
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "update list failed", 500


@app.route('/api/wordlists', methods=['DELETE'])
def delete_wordlists():
    doomed = request.form.getlist('deletelist')
    if len(doomed):
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            format_list = ['%s'] * len(doomed)
            format_args = ', '.join(format_list)
            sql = "delete from wordlist where id in (%s)" % format_args
            args = [int(x) for x in doomed]
            cursor.execute(sql, args)
            dbh.commit()

    return 'OK'


@app.route('/api/wordlists', methods=['GET'])
def get_wordlists():
    """
    request format is

    ?wordlist_id=n,n,n ... - optional.  only return info for the given lists.

    """

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        wordlist_ids = request.args.get('wordlist_id')
        if wordlist_ids:
            wordlist_ids = wordlist_ids.split(',')
            wordlist_ids = list(set(wordlist_ids))
            where_clause = "where wordlist.id in (%s)" % (','.join(['%s'] * len(wordlist_ids)))
        else:
            where_clause = ''

        sql = """
with wordlist_counts as
(
    select wordlist_id, sum(c) lcount from
    (
        select wordlist_id, count(*) c
        from wordlist_unknown_word
        group by wordlist_id
        union all
        select wordlist_id, count(*) c
        from wordlist_known_word
        group by wordlist_id
    ) a
    group by wordlist_id
)
select name, id wordlist_id, ifnull(lcount, 0) count, sqlcode
from wordlist
left join wordlist_counts wc on wc.wordlist_id = wordlist.id
%(where_clause)s
order by name
        """ % {
            'where_clause': where_clause
        }

        cursor.execute(sql, wordlist_ids)
        rows = cursor.fetchall()

        # maps list id to list info
        dict_result = {}

        for r in rows:
            # TODO - the connector is returning the count as a string, find out WTF

            list_type = 'empty'
            if bool(r['sqlcode']):
                list_type = 'smart'
            elif r['count'] > 0:
                list_type = 'standard'

            dict_result[r['wordlist_id']] = {}
            dict_result[r['wordlist_id']]['name'] = r['name']
            dict_result[r['wordlist_id']]['wordlist_id'] = r['wordlist_id']
            dict_result[r['wordlist_id']]['list_type'] = list_type
            dict_result[r['wordlist_id']]['count'] = int(r['count'])

            if r['sqlcode']:
                cursor.execute(r['sqlcode'])
                smartlist_rows = cursor.fetchall()
                dict_result[r['wordlist_id']]['count'] = len(smartlist_rows)

        result = list(dict_result.values())
        jsonschema.validate(result, dlernen.dlernen_json_schema.WORDLISTS_SCHEMA)
        return result


@app.route('/api/wordlists', methods=['PUT'])
def refresh_wordlists():
    """
    this is used when a word in some wordlist's unknowns has been defined.  we are given the word
    and the newly minted word id.  we'll look for every wordlist where the given word was an unknown,
    remove it from the unknowns and put it into the knowns.

    payload:
    {
        'word': 'whatever',
        'word_id':  <word_id>
    }
    """

    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.REFRESH_WORDLISTS_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = """
            select wordlist_id
            from wordlist_unknown_word
            where word = %(word)s
            """
            cursor.execute(sql, {'word': payload['word']})
            rows = cursor.fetchall()

            sql = """
            delete from wordlist_unknown_word
            where word = %(word)s
            """
            cursor.execute(sql, {'word': payload['word']})

            insert_args = [(r['wordlist_id'], payload['word_id']) for r in rows]
            if insert_args:
                sql = """
                insert ignore
                into wordlist_known_word (wordlist_id, word_id)
                values (%s, %s)
                """

                cursor.executemany(sql, insert_args)
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "refresh wordlists failed", 500


# TODO - implement a get-by-word version of this.
@app.route('/api/wordlists/<int:word_id>')
def get_wordlists_by_word_id(word_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # find standard lists that this word is in
        sql = """
        select
        wl.id wordlist_id
        from wordlist wl
        inner join wordlist_known_word wkw
        on wkw.wordlist_id = wl.id
        where word_id = %s
        order by wl.name
        """
        cursor.execute(sql, (word_id,))
        rows = cursor.fetchall()
        static_lists = [r['wordlist_id'] for r in rows]

        # find smart lists that this word is in!
        # get all the sql
        sql = """
        select name, sqlcode, id wordlist_id
        from wordlist
        where sqlcode is not null
        """

        smart_lists = []
        cursor.execute(sql)
        code_results = cursor.fetchall()
        for r in code_results:
            sqlcode = r['sqlcode'].strip()
            if not sqlcode:
                continue

            cursor.execute(r['sqlcode'])
            results_for_list = cursor.fetchall()
            results_for_list = [x['word_id'] for x in results_for_list]
            if word_id in results_for_list:
                smart_lists.append(r['wordlist_id'])

        wordlist_ids = static_lists + smart_lists

        result = []
        if wordlist_ids:
            args = ','.join([str(x) for x in wordlist_ids])
            url = url_for('get_wordlists', wordlist_id=args)
            url = "%s/%s" % (Config.DB_URL, url)
            r = requests.get(url)

            result = json.loads(r.text)
            result = sorted(result, key=lambda x: x['name'].casefold())

        # validation happens in get_wordlists so we don't need to do it here.

        return result


@app.route('/api/word/metadata')
def word_metadata():
    """
    get all of the attributes for all parts of speech.  if a word is given (not a word_id), then enrich
    the POS data with all the attribute values for the word.  the data structure returned will be used in
    the UI to edit the word and its attribute values.

    optional arguments:
    word - the word for which we are getting all the things.

    if a word is not provided then we only return enough info to create and populate an empty form.
    """

    word = request.args.get('word')

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
with pos_info as
(
select
    p.id pos_id,
    p.name pos_name,
    a.id attribute_id,
    a.attrkey,
    pf.sort_order
from pos p
inner join pos_form pf on pf.pos_id = p.id
inner join attribute a on a.id = pf.attribute_id
)
select
        case
        when mashup_v.attrvalue_id is not null then
        concat(pos_info.pos_id, '-', pos_info.attrkey, '-', mashup_v.attrvalue_id)
        else concat(pos_info.pos_id, '-', pos_info.attrkey)
        end
        field_key,
        case
        when mashup_v.word_id is not null then
        concat(pos_info.pos_id, '-', pos_info.pos_name, '-', mashup_v.word_id)
        else concat(pos_info.pos_id, '-', pos_info.pos_name)
        end tag,
        pos_info.pos_name,
        pos_info.sort_order,
        pos_info.attrkey,
        mashup_v.word,
        mashup_v.attrvalue
from pos_info
left join  mashup_v on mashup_v.pos_id = pos_info.pos_id and mashup_v.attribute_id = pos_info.attribute_id
"""

        if word:
            sql += " and mashup_v.word = %(word)s"
            cursor.execute(sql, {'word': word})
        else:
            sql += " and mashup_v.word is NULL"
            cursor.execute(sql)

        rows = cursor.fetchall()
        # pprint(rows)
        result = {}
        for r in rows:
            if r['pos_name'] not in result:
                result[r['pos_name']] = {
                    'pos_name': r['pos_name'],
                    'tag': r['tag'],
                    'pos_fields': []
                }
            d = {
                k: r.get(k) for k in r.keys() & {
                    'attrkey',
                    'sort_order',
                    'field_key'
                }
            }
            if r['attrvalue']:
                d['attrvalue'] = r['attrvalue']
            result[r['pos_name']]['pos_fields'].append(d)

        # TODO - define schema for the data structure returned here.
        for v in result.values():
            v['pos_fields'] = sorted(v['pos_fields'], key=lambda x: x['sort_order'])
        result = list(result.values())
        return result


@app.route('/')
def home():
    return render_template('home.html')


def get_lookup_render_template(word, wordlist_id=None):
    url = "%s/api/word/%s" % (Config.DB_URL, word)
    results = None
    r = requests.get(url)
    if r.status_code == 404:
        pass
    elif r.status_code == 200:
        results = r.json()
        # pprint(results)
    return render_template('lookup.html',
                           word=word,
                           return_to_wordlist_id=wordlist_id,
                           results=results)


@app.route('/lookup/<string:word>', methods=['GET'])
def lookup_by_get(word):
    wordlist_id = request.args.get('wordlist_id')
    return get_lookup_render_template(word, wordlist_id)


@app.route('/lookup', methods=['POST'])
def lookup_by_post():
    word = request.form.get('lookup')
    wordlist_id = request.form.get('wordlist_id')
    return get_lookup_render_template(word, wordlist_id)


@app.route('/wordlists')
def wordlists():
    url = "%s/api/wordlists" % Config.DB_URL
    r = requests.get(url)
    result = json.loads(r.text)

    return render_template('wordlists.html', rows=result)


@app.route('/healthcheck')
def healthcheck():
    return 'OK'


@app.route('/dbcheck')
def dbcheck():
    # TODO: have to disable mysql server autostart to test no-connection condition
    pass


@app.route('/list_attributes/<int:wordlist_id>')
def list_attributes(wordlist_id):
    url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
    r = requests.get(url)
    result = r.json()

    return render_template('list_attributes.html',
                           wordlist=result,
                           return_to_wordlist_id=wordlist_id)


@app.route('/wordlist/<int:wordlist_id>')
def wordlist(wordlist_id):
    nchunks = request.args.get('nchunks', app.config['NCHUNKS'], type=int)
    url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
    r = requests.get(url)
    if r.status_code == 404:
        return redirect('/wordlists')

    result = r.json()
    if result['list_type'] == 'smart':
        words = chunkify(result['known_words'], nchunks=nchunks)
        return render_template('smart_wordlist.html',
                               result=result,
                               words=words)

    known_words = chunkify(result['known_words'], nchunks=nchunks)
    unknown_words = chunkify(result['unknown_words'], nchunks=nchunks)

    return render_template('wordlist.html',
                           result=result,
                           known_words=known_words,
                           unknown_words=unknown_words)


@app.route('/addlist', methods=['POST'])
def addlist():
    payload = {
        'name': request.form['name'].strip(),
        'citation': request.form.get('citation')
    }

    url = "%s/api/wordlist" % Config.DB_URL
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        return redirect('/wordlists')

    raise Exception("something went wrong in /api/wordlist POST: %s" % r.text)


@app.route('/deletelist', methods=['POST'])
def deletelist():
    doomed = request.form.getlist('deletelist')
    url = "%s/api/wordlists" % Config.DB_URL
    payload = {
        'deletelist': doomed
    }

    r = requests.delete(url, data=payload)
    if r.status_code == 200:
        return redirect('/wordlists')
    raise Exception("something went wrong in /api/wordlists: %s" % r.text)


@app.route('/edit_list', methods=['POST'])
def edit_list():
    payload = {
        'name': request.form['name'],
        'citation': request.form.get('citation'),
        'sqlcode': request.form.get('sqlcode')
    }
    wordlist_id = request.form['wordlist_id']

    url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code == 200:
        target = url_for('wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    raise Exception("something went wrong in /api/wordlist PUT: %s" % r.text)


@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    word = request.form['word'].strip()
    wordlist_id = request.form['wordlist_id']

    # TODO - for now, we can only add a word to a wordlist, not a word_id.
    payload = None
    url = "%s/api/word/%s" % (Config.DB_URL, word)
    r = requests.get(url)
    if r.status_code == 404:
        payload = {
            "words": [
                word
            ]
        }
    elif r.status_code == 200:
        obj = r.json()
        payload = {
            "words": [
                word
            ]
        }

    if not payload:
        raise Exception("add_to_list could not make payload")

    url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code != 200:
        raise Exception("well, shit")

    target = url_for('wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@app.route('/update_notes', methods=['POST'])
def update_notes():
    payload = {
        'notes': request.form['notes']
    }
    wordlist_id = request.form['wordlist_id']

    url = "%s/api/wordlist/%s" % (Config.DB_URL, wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code == 200:
        target = url_for('wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    raise Exception("something went wrong in /api/wordlist PUT: %s" % r.text)


@app.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    wordlist_id = request.form['wordlist_id']
    known_deleting = request.form.getlist('known_wordlist')
    unknown_deleting = request.form.getlist('unknown_wordlist')

    for word_id in known_deleting:
        url = "%s/api/wordlist/%s/%s" % (Config.DB_URL, wordlist_id, int(word_id))
        r = requests.delete(url)

    for word in unknown_deleting:
        url = "%s/api/wordlist/%s/%s" % (Config.DB_URL, wordlist_id, word)
        r = requests.delete(url)

    # TODO - change API to allow batch delete.  we could do this with a single request

    target = url_for('wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@app.route('/word/<string:word>')
def edit_word_form(word):
    wordlist_id = request.args.get('wordlist_id')

    url = "%s/api/word/metadata?word=%s" % (Config.BASE_URL, word)
    r = requests.get(url)
    pos_infos = r.json()
    return render_template('addword.html',
                           word=word,
                           wordlist_id=wordlist_id,
                           return_to_wordlist_id=wordlist_id,
                           pos_infos=pos_infos)


@app.route('/update_dict', methods=['POST'])
def update_dict():
    tag = request.form.get('tag')
    if not tag:
        raise Exception("select something")

    # tag is <pos_id>-<pos_name>-<word_id> for the editing case and <pos_id>-<pos_name> for the adding case.

    tag_parts = tag.split('-')
    pos_id = tag_parts[0]
    word_id = None
    if len(tag_parts) > 2:
        word_id = tag_parts[2]

    # get all the attribute info from the form and turn it into a dict.
    attrs_from_form = {}
    for f in request.form.keys():
        field_key_parts = f.split('-')
        p = field_key_parts[0]
        if p != pos_id:
            continue
        attrkey = field_key_parts[1]
        if attrkey not in attrs_from_form:
            attrs_from_form[attrkey] = {}
            attrvalue = request.form.get(f)
            if attrvalue:
                attrs_from_form[attrkey]['attrvalue'] = attrvalue
            if len(field_key_parts) > 2:
                attrs_from_form[attrkey]['attrvalue_id'] = int(field_key_parts[2])

    if not word_id:
        pos_name = tag_parts[1]
        word = request.form.get('word')
        if word is not None:
            word = word.strip()
        if not word:
            raise Exception('word for add_word is empty')
        payload = {
            'word': word,
            'pos_name': pos_name,
            'attributes': []
        }

        for k in attrs_from_form.keys():
            attrvalue = attrs_from_form[k].get('attrvalue')
            if attrvalue:
                payload['attributes'].append(
                    {
                        'attrkey': k,
                        'attrvalue': attrvalue
                    }
                )

        url = "%s/api/word" % Config.DB_URL
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            raise Exception("failed to insert word '%s'" % word)

        obj = r.json()

        # remove this word from the unknown wordlists and put the word_id into the known words for those lists.

        refresh_payload = {
            'word': word,
            'word_id': obj['word_id']
        }
        url = "%s/api/wordlists" % Config.DB_URL
        r = requests.put(url, json=refresh_payload)
        if r.status_code != 200:
            raise Exception("failed to refresh word lists")

        wordlist_id = request.form.get('wordlist_id')
        if wordlist_id:
            target = url_for('wordlist', wordlist_id=wordlist_id)
        else:
            # if we didn't add a word to any list, return to the editing form for this word.
            target = url_for('edit_word_form', word=word)

        return redirect(target)

    # we are updating.  figure out all the attribute values we have to add/remove/update.

    # go through the contents of the form and figure out what changes to make.  cases:
    #
    # 1.  if there is an attrvalue_id but no value, we are deleting.
    # 2.  if there is an attrvalue but no attrvalue id, we are adding.
    # 3.  if both are present, we are updating.

    payload = {
        "attributes_adding": [],
        "attributes_deleting": [],
        "attributes_updating": []
    }

    word = request.form.get('word')
    if word is not None:
        word = word.strip()
    if word:
        payload['word'] = word.strip()

    # pprint(attrs_from_form)
    for k, v in attrs_from_form.items():
        if 'attrvalue' not in v and 'attrvalue_id' in v:
            payload["attributes_deleting"].append(int(v['attrvalue_id']))
        elif 'attrvalue_id' not in v:
            payload["attributes_adding"].append(
                {
                    'attrkey': k,
                    'attrvalue': v['attrvalue']
                }
            )
        else:
            payload['attributes_updating'].append(v)

    url = "%s/api/word/%s" % (Config.DB_URL, word_id)
    r = requests.put(url, json=payload)

    wordlist_id = request.form.get('wordlist_id')
    if wordlist_id:
        target = url_for('wordlist', wordlist_id=wordlist_id)
    else:
        # if we didn't add a word to any list, return to the editing form for this word.
        target = url_for('edit_word_form', word=word)

    return redirect(target)
