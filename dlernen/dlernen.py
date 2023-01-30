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


def get_word_ids_from_list_ids(limit, list_ids, recent, attrkey):
    """
    returns a list containing 0 or more unique word ids.
    """

    results = []
    list_ids = list_ids.split(',')

    for list_id in list_ids:
        # use the API so we don't have to worry about whether any are smart lists
        url = "%s/api/wordlist/%s" % (Config.DB_URL, list_id)
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

    list_id=n,n,n - optional.  restrict the word ids to those in the given lists.

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

        list_ids = request.args.get('list_id')
        if list_ids:
            word_ids = get_word_ids_from_list_ids(limit, list_ids, recent, attrkey)
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


@app.route('/healthcheck')
def healthcheck():
    return 'OK'


@app.route('/dbcheck')
def dbcheck():
    # TODO: have to disable mysql server autostart to test no-connection condition
    pass


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
    (word, pos_id) is a unique key, it is possible to return more than
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

    #pprint(payload)
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

            request_attrkeys = {a['attrkey'].strip() for a in payload['attributes']}
            undefined_attrkeys = request_attrkeys - defined_attrkeys
            if len(undefined_attrkeys) > 0:
                message = "attribute keys not defined:  %s" % ', '.join(list(undefined_attrkeys))
                cursor.execute('rollback')
                return message, 400

            # check that attrvalues are all strings len > 0
            payload_attrvalues = {a['attrvalue'].strip() for a in payload['attributes']}
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

            for a in payload['attributes']:
                attrvalue = a['attrvalue'].strip()

                link_d = {
                    "word_id": word_id,
                    "attribute_id": attrdict[a['attrkey']],
                    "attrvalue": attrvalue
                }

                sql = """insert into word_attribute (word_id, attribute_id, attrvalue)
                values (%(word_id)s, %(attribute_id)s, %(attrvalue)s)
                """
                cursor.execute(sql, link_d)

            cursor.execute('commit')

            return get_word_by_id(word_id)  # this is already validated and jsonified

        except Exception as e:
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
    # zero-length attribute list is ok
    # attrvalue ids exist and belong to the word
    # new attrvalues are all strings len > 0.

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = """
            select attrvalue_id
            from mashup_v
            where word_id = %(word_id)s
            and attrvalue_id is not null
            """
            cursor.execute(sql, {'word_id': word_id})
            rows = cursor.fetchall()
            defined_attrvalue_ids = {r['attrvalue_id'] for r in rows}

            if len(defined_attrvalue_ids) == 0:
                # word_id is bogus
                message = "word_id %s not found" % word_id
                cursor.execute('rollback')
                return message, 404

            payload_attrvalue_ids = {a['attrvalue_id'] for a in payload['attributes']}
            undefined_attrvalue_ids = payload_attrvalue_ids - defined_attrvalue_ids
            if len(undefined_attrvalue_ids) > 0:
                message = "attrvalue_ids not defined:  %s" % ', '.join(list(undefined_attrvalue_ids))
                cursor.execute('rollback')
                return message, 400

            word = None
            if 'word' in payload:
                word = payload['word'].strip()
            if word == '':
                message = 'word cannot be empty string'
                return message, 400

            # check that attrvalues are all strings len > 0
            payload_attrvalues = {a['attrvalue'].strip() for a in payload['attributes']}
            bad_attrvalues = list(filter(lambda x: not bool(x), payload_attrvalues))
            if len(bad_attrvalues) > 0:
                message = "attribute values cannot be empty strings"
                cursor.execute('rollback')
                return message, 400

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
            for a in payload['attributes']:
                d = {
                    'attrvalue': a['attrvalue'].strip(),
                    'attrvalue_id': a['attrvalue_id']
                }
                cursor.execute(sql, d)

            cursor.execute('commit')

            return get_word_by_id(word_id)  # this is already validated and jsonified

        except Exception as e:
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
                pprint(rows_to_insert)
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


@app.route('/list_attributes/<int:list_id>')
def list_attributes(list_id):
    url = "%s/api/list_attributes/%s" % (Config.DB_URL, list_id)
    r = requests.get(url)
    result = json.loads(r.text)

    return render_template('list_attributes.html', wl_row=result)


@app.route('/api/wordlist/<int:list_id>/metadata')
def get_list_attributes(list_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
    select
        id wordlist_id, name, citation, ifnull(sqlcode, '') sqlcode
     from wordlist
    where id = %s
    """
        cursor.execute(sql, (list_id,))
        wl_row = cursor.fetchone()

        jsonschema.validate(wl_row, dlernen.dlernen_json_schema.WORDLIST_METADATA_SCHEMA)

        return wl_row


@app.route('/api/wordlist/<int:list_id>')
def get_wordlist(list_id):
    # uses WORDLIST_SCHEMA
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            id wordlist_id,
            name,
            citation,
            ifnull(notes, '') notes,
            ifnull(sqlcode, '') sqlcode
        from wordlist
        where id = %s
        """
        cursor.execute(sql, (list_id,))
        wl_row = cursor.fetchone()
        if not wl_row:
            return "wordlist %s not found" % list_id, 404

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
                  ifnull(m2.attrvalue, '') article
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
                ifnull(m2.attrvalue, '') article
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

            cursor.execute(known_words_sql, (list_id,))

        known_words = cursor.fetchall()

        result['known_words'] = known_words

        unknown_words_sql = """
        select
        ww.word word
        from wordlist_unknown_word ww
        where ww.wordlist_id = %s
        order by ww.word
        """

        cursor.execute(unknown_words_sql, (list_id,))
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


def add_words_to_list(cursor, list_id, words):
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
    wkw_tuples = [(list_id, r['word_id']) for r in rows]
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
        wuw_tuples = [(list_id, x) for x in unknown_words]
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
            cursor.execute("select last_insert_id() list_id")
            result = cursor.fetchone()
            list_id = result['list_id']

            # figure out which words are known and not known
            if words:
                add_words_to_list(cursor, list_id, words)

            cursor.execute('commit')

            return get_wordlist(list_id)
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "create list failed", 500


@app.route('/api/wordlist/<int:list_id>', methods=['DELETE'])
def delete_wordlist(list_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "delete from wordlist where id = %s"
            cursor.execute(sql, (list_id,))
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:list_id>/<int:word_id>', methods=['DELETE'])
def delete_from_wordlist_by_id(list_id, word_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "select sqlcode from wordlist where id = %s"
            cursor.execute(sql, (list_id,))
            row = cursor.fetchone()
            if row and row['sqlcode']:
                cursor.execute('rollback')
                return "can't delete words from smart list", 400
            sql = "delete from wordlist_known_word where wordlist_id = %s and word_id = %s"
            cursor.execute(sql, (list_id, word_id))
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:list_id>/<string:word>', methods=['DELETE'])
def delete_from_wordlist_by_word(list_id, word):
    # removes from unknown words only
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            word = word.strip()
            if word:
                cursor.execute('start transaction')
                sql = "select sqlcode from wordlist where id = %s"
                cursor.execute(sql, (list_id,))
                row = cursor.fetchone()
                if row and row['sqlcode']:
                    cursor.execute('rollback')
                    return "can't delete words from smart list", 400
                sql = "delete from wordlist_unknown_word where wordlist_id = %s and word = %s"
                cursor.execute(sql, (list_id, word))
                cursor.execute('commit')
            return "OK"
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "delete list failed", 500


@app.route('/api/wordlist/<int:list_id>', methods=['PUT'])
def update_wordlist(list_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen.dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        print("shit1")
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

    if sqlcode and words:
        return "can't modify list with sqlcode and words", 400

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # this is well-behaved if citation and sqlcode are not given.
        cursor.execute('start transaction')

        existing_list = get_wordlist(list_id)
        if existing_list['list_type'] == 'smart' and words and sqlcode != '':
            # if sqlcode is the empty string, then this is ok, because it means we are going to
            # clear out the existing sqlcode.
            cursor.execute('rollback')
            return "can't add words to smart list", 400

        if existing_list['list_type'] == 'standard' and sqlcode:
            cursor.execute('rollback')
            return "can't add code to existing list", 400

        try:
            update_args = {
                'citation': citation,
                'notes': notes,
                'name': name,
                'sqlcode': sqlcode,
                'list_id': list_id
            }

            cursor.execute('start transaction')
            sql = """
            update wordlist
            set `name` = case when %(name)s is not null and length(%(name)s) > 0
                then %(name)s
                else name
            end,
            citation = case when %(citation)s is not null and length(%(citation)s) > 0
                then %(citation)s
                else citation
            end,
            sqlcode = case when %(sqlcode)s is not null
                then %(sqlcode)s
                else sqlcode
            end,
            notes = case when %(notes)s is not null and length(%(notes)s) > 0
                then %(notes)s
                else notes
            end
            where id = %(list_id)s
            """
            cursor.execute(sql, update_args)

            if words:
                add_words_to_list(cursor, list_id, words)

            cursor.execute('commit')

            return get_wordlist(list_id)
        except Exception as e:
            pprint(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            cursor.execute('rollback')
            return "create list failed", 500


@app.route('/wordlist/<int:list_id>')
def wordlist(list_id):
    nchunks = request.args.get('nchunks', app.config['NCHUNKS'], type=int)
    url = "%s/api/wordlist/%s" % (Config.DB_URL, list_id)
    r = requests.get(url)
    result = json.loads(r.text)

    if result['list_type'] == 'smart':
        words = chunkify(result['known_words'], nchunks=nchunks)
        return render_template('smart_wordlist.html',
                               result=result,
                               list_id=list_id,
                               words=words,
                               source_is_url=result['source_is_url'],
                               words_count=len(result['known_words']))

    known_words = chunkify(result['known_words'], nchunks=nchunks)
    unknown_words = chunkify(result['unknown_words'], nchunks=nchunks)

    return render_template('wordlist.html',
                           result=result,
                           list_id=list_id,
                           source_is_url=result['source_is_url'],
                           known_words=known_words,
                           known_words_count=len(result['known_words']),
                           unknown_words_count=len(result['unknown_words']),
                           unknown_words=unknown_words)


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

    ?list_id=n,n,n ... - optional.  only return info for the given lists.

    """

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        list_ids = request.args.get('list_id')
        if list_ids:
            list_ids = list_ids.split(',')
            list_ids = list(set(list_ids))
            where_clause = "where wordlist.id in (%s)" % (','.join(['%s'] * len(list_ids)))
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
        union
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

        cursor.execute(sql, list_ids)
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

        # json_schema.WORDLISTS_SCHEMA
        result = list(dict_result.values())
        jsonschema.validate(result, dlernen.dlernen_json_schema.WORDLISTS_SCHEMA)
        return result


@app.route('/api/wordlists/<int:word_id>')
def get_wordlists_for_word(word_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # find standard lists that this word is in
        sql = """
        select
        wl.id list_id
        from wordlist wl
        inner join wordlist_known_word wkw
        on wkw.wordlist_id = wl.id
        where word_id = %s
        order by wl.name
        """
        cursor.execute(sql, (word_id,))
        rows = cursor.fetchall()
        static_lists = [r['list_id'] for r in rows]

        # find smart lists that this word is in!
        # get all the sql
        sql = """
        select name, sqlcode, id list_id
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
                smart_lists.append(r['list_id'])

        list_ids = static_lists + smart_lists

        result = []
        if list_ids:
            args = ','.join([str(x) for x in list_ids])
            url = url_for('get_wordlists', list_id=args)
            url = "%s/%s" % (Config.DB_URL, url)
            r = requests.get(url)

            result = json.loads(r.text)
            result = sorted(result, key=lambda x: x['name'].casefold())

        # validation happens in get_wordlists so we don't need to do it here.

        return result


@app.route('/')
@app.route('/wordlists')
def wordlists():
    url = "%s/api/wordlists" % Config.DB_URL
    r = requests.get(url)
    result = json.loads(r.text)

    return render_template('wordlists.html', rows=result)


@app.route('/addlist', methods=['POST'])
def addlist():
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        newlist = request.form['name'].strip()
        citation = request.form['citation'].strip()
        sql = "insert ignore into wordlist (name, citation) values (%s, %s)"
        cursor.execute(sql, (newlist, citation))
        dbh.commit()

        return redirect('/wordlists')
        # todo:  error handling for empty list name, list that already exists


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
    raise Exception("something went wrong in /api/wordlists")


@app.route('/edit_list', methods=['POST'])
def edit_list():
    name = request.form['name']
    citation = request.form['citation']
    sqlcode = request.form['sqlcode']
    id = request.form['list_id']
    sql = "update wordlist set name = %s, citation = %s, sqlcode = %s where id = %s"
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(sql, (name, citation, sqlcode, id))
        dbh.commit()

    target = url_for('wordlist', list_id=id)
    return redirect(target)


@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    word = request.form['word'].strip()
    list_id = request.form['list_id']

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # count the number of times word is in the word table.
        #
        # if it is 0, it goes into the unknown word table.
        # if it is 1, it goes into the known word table.
        # otherwise, present multiple choice.

        sql = """
    select word, id
    from word
    where word = %s
    """
        cursor.execute(sql, (word,))
        rows = cursor.fetchall()
        count = len(rows)

        if count == 0:
            sql = """
    insert ignore
    into wordlist_unknown_word (wordlist_id, word) 
    values (%s, %s)
    """
            cursor.execute(sql, (list_id, word))
            dbh.commit()
            target = url_for('wordlist', list_id=list_id)
            return redirect(target)

        if count == 1:
            row = rows[0]
            word_id = row['id']
            sql = """
    insert ignore
    into wordlist_known_word (wordlist_id, word_id)
    values (%s, %s)
    """
            cursor.execute(sql, (list_id, word_id))
            dbh.commit()
            target = url_for('wordlist', list_id=list_id)
            return redirect(target)

        pos_infos, word = get_data_for_addword_form(word=word)

        return render_template('addword.html',
                               word=word,
                               list_id=list_id,
                               return_to_list_id=list_id,
                               pos_infos=pos_infos)
        # todo:  validate input: word in not bad script, list id is int


@app.route('/update_notes', methods=['POST'])
def update_notes():
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        notes = request.form['notes']
        id = request.form['list_id']
        sql = "update wordlist set notes = %s where id = %s"
        cursor.execute(sql, (notes, id))
        dbh.commit()

        target = url_for('wordlist', list_id=id)
        return redirect(target)


@app.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    list_id = request.form['list_id']
    known_deleting = request.form.getlist('known_wordlist')

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if len(known_deleting):
            format_list = ['%s'] * len(known_deleting)
            format_args = ', '.join(format_list)

            sql = """
    delete from wordlist_known_word
    where wordlist_id = %%s
    and word_id in (%s)
    """ % format_args

            args = [list_id] + known_deleting
            cursor.execute(sql, args)
            dbh.commit()

        unknown_deleting = request.form.getlist('unknown_wordlist')

        if len(unknown_deleting):
            format_list = ['%s'] * len(unknown_deleting)
            format_args = ', '.join(format_list)

            sql = """
    delete from wordlist_unknown_word
    where wordlist_id = %%s
    and word in (%s)
    """ % format_args

            args = [list_id] + unknown_deleting
            cursor.execute(sql, args)
            dbh.commit()

        target = url_for('wordlist', list_id=list_id)
        return redirect(target)
        # todo:  validate input: word in not bad script, list id is int


def get_pos_info_for_form(cursor):
    """
    get all the part-of-speech info needed to construct the addword form.
    the data returned is for POS only and is not specific to any word.

    returns a dictionary that looks like this:

    pos_id => field_key (pos_id-attr_id-attrkey) => {
         field_key:
         attrkey:
         pos_name:
         sort_order:
    }
    """
    sql = """
select
    p.id pos_id,
    p.name pos_name,
    a.id attribute_id,
    a.attrkey,
    sort_order
from pos p
inner join pos_form pf on pf.pos_id = p.id
inner join attribute a on a.id = pf.attribute_id
order by p.id, sort_order
"""

    cursor.execute(sql)
    pos_list = cursor.fetchall()

    form_dict = {}
    for pos in pos_list:
        if not form_dict.get(pos['pos_id']):
            form_dict[pos['pos_id']] = {}
        k = '%s-%s-%s' % (pos['pos_id'], pos['attribute_id'], pos['attrkey'])
        form_dict[pos['pos_id']][k] = {
            'field_key': k,
            'pos_name': pos['pos_name'],
            'attrkey': pos['attrkey'],
            'sort_order': pos['sort_order']
        }

    return form_dict


def populate_form_dict(cursor, form_dict, **kwargs):
    """
    populate the form_dict with attribute values for the given word id
    """
    word_id = kwargs.get('word_id')
    word = kwargs.get('word')

    if bool(word_id) == bool(word):
        raise Exception("exactly one of word_id and word must be set")

    checked_pos = None

    if word_id:
        sql = """
select
    word_id, word, pos_id, pos_name, attribute_id, attrkey,
    ifnull(attrvalue, '') attrvalue, sort_order
from mashup_v
where word_id in
(
        select id from word
        where word in (
              select word from word where id = %s
        )
)
"""
        cursor.execute(sql, (word_id,))
    else:
        sql = """
select
    word_id, word, pos_id, pos_name, attribute_id, attrkey,
    ifnull(attrvalue, '') attrvalue, sort_order
from mashup_v
where word_id in
(
        select id from word
        where word in (
              select word from word where word = %s
        )
)
"""
        cursor.execute(sql, (word,))

    value_rows = cursor.fetchall()
    for r in value_rows:
        word = r['word']
        k = '%s-%s-%s' % (r['pos_id'], r['attribute_id'], r['attrkey'])
        pos_id = r['pos_id']
        form_dict[pos_id][k]['attrvalue'] = r['attrvalue']
        if r['word_id'] == word_id:
            checked_pos = r['pos_id']

    return checked_pos, word


def get_data_for_addword_form(**kwargs):
    word = kwargs.get('word')
    word_id = kwargs.get('word_id')

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        form_dict = get_pos_info_for_form(cursor)

        if word_id:
            word_id = int(word_id)
            # this is harder.  in this case we have an existing word.  we need
            # to fill in all the attribute values for it, for all parts of
            # speech for this word that exist in this word list.

            checked_pos, word = populate_form_dict(cursor, form_dict, word_id=word_id)
        elif word:
            checked_pos, word = populate_form_dict(cursor, form_dict, word=word)
        else:
            checked_pos = word = None

        pos_infos = []
        for k in list(form_dict.keys()):
            pos_fields = [x for x in list(form_dict[k].values())]
            l = sorted(pos_fields, key=lambda x: x['sort_order'])
            pos_info = {
                'pos_id': k,
                'pos_fields': l,
                'pos_name': l[0]['pos_name']
            }
            if checked_pos == k:
                pos_info['checked'] = True

            pos_infos.append(pos_info)

        pos_infos = sorted(pos_infos, key=lambda x: x['pos_id'])
        return pos_infos, word


@app.route('/word')
def add_word_from_form():
    pos_infos, word = get_data_for_addword_form()
    return render_template('addword.html',
                           pos_infos=pos_infos)


@app.route('/word/<int:word_id>')
def update_word_by_id(word_id):
    list_id = request.args.get('list_id')

    url = "%s/api/wordlists/%s" % (Config.DB_URL, word_id)
    r = requests.get(url)
    wordlists = json.loads(r.text)

    pos_infos, word = get_data_for_addword_form(word_id=word_id)
    return render_template('addword.html',
                           word=word,
                           list_id=list_id,
                           return_to_list_id=list_id,
                           wordlists=wordlists,
                           pos_infos=pos_infos)


@app.route('/word/<string:word>')
def update_word_from_form(word):
    list_id = request.args.get('list_id')

    pos_infos, word = get_data_for_addword_form(word=word)
    return render_template('addword.html',
                           word=word,
                           list_id=list_id,
                           return_to_list_id=list_id,
                           pos_infos=pos_infos)


@app.route('/add_to_dict', methods=['POST'])
def add_to_dict():
    # for user convenience, all the parts of speech and their attributes
    # can be entered in one form.  extracting the values will be painful.
    # have to look at what POS was selected, then find the form values for it.

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if 'pos' not in request.form:
            raise Exception("select something")

        # add the word to get the word_id
        form_pos_id = request.form['pos']

        # get the name of the pos
        q = """
    select name
    from pos
    where id = %s
    """

        cursor.execute(q, (form_pos_id,))
        r = cursor.fetchone()
        pos_name = r['name']

        word = request.form['word'].strip()
        if not word:
            raise Exception("no word")

        if pos_name == 'Noun':
            word = word.capitalize()

        w_sql = """
    insert ignore into word (pos_id, word)
    values (%s, %s)
    """
        cursor.execute(w_sql, (form_pos_id, word))

        id_sql = "select last_insert_id() word_id"
        cursor.execute(id_sql)
        r = cursor.fetchone()
        word_id = r['word_id']

        # if word_id is 0, then the insert ignore didn't do anything because the
        # word was already there.  go get it.
        if word_id == 0:
            sql = """
    select id
    from word
    where pos_id = %s and word = %s
    """
            cursor.execute(sql, (form_pos_id, word))
            r = cursor.fetchone()
            word_id = r['id']

        # all the text fields have names of the form <pos_id>-<attribute_id>-<attrkey>.
        # look for all the form fields that start with the pos_id.

        values = []
        placeholders = []
        for k in list(request.form.keys()):
            splitkey = k.split('-')
            if len(splitkey) < 3:
                continue
            pos_id, attr_id, attrkey = splitkey[:3]
            if pos_id == form_pos_id and request.form[k]:
                placeholder = "(%s, %s, %s)"  # word_id, attr_id, value
                placeholders.append(placeholder)
                value = request.form[k].strip()
                if pos_name == 'Noun' and attrkey == 'plural':
                    value = value.capitalize()

                values += [word_id, attr_id, value]

        if len(values) > 0:
            wa_sql = """
    insert into word_attribute (word_id, attribute_id, value)
    values
    %s
    on duplicate key update
    value=values(value)
    """ % ', '.join(placeholders)

            cursor.execute(wa_sql, values)

        # now remove the word from unknown words and put it into known words.
        list_id = request.form.get('list_id')
        del_sql = """
    delete from wordlist_unknown_word
    where word = %s
    and wordlist_id = %s
    """
        cursor.execute(del_sql, (word, list_id))

        ins_sql = """
    insert ignore into wordlist_known_word (wordlist_id, word_id)
    values (%s, %s)
    """
        cursor.execute(ins_sql, (list_id, word_id))

        dbh.commit()

        if list_id:
            target = url_for('wordlist', list_id=list_id)
        else:
            # if we didn't add a word to any list, return to the editing form for this word.
            target = url_for('update_word_by_id', word_id=word_id)

        return redirect(target)
