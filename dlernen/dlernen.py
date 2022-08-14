import werkzeug.exceptions
from flask import Flask, request, render_template, redirect, url_for, jsonify
from pprint import pprint
from mysql.connector import connect
from dlernen.config import Config
from dlernen import quiz_sql
import requests
import json
from contextlib import closing

app = Flask(__name__)
app.config.from_object(Config)


def error_handler(e):
    pprint("error handler>>>>>>>>>>>>>>>>>>>>>>>>>")
    return str(e), 400


app.register_error_handler(500, error_handler)


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
    ids = json.loads(request.form.get('arr'))
    pprint(ids)
    return jsonify(request.form)


@app.route('/api/choose_words')
def choose_words():
    """
    request format is

    recent={true|false} - optional, default is false
    if true, select the word ids by added date, most recent first
    if false or not specified, selects by rand()

    limit=n - optional.  restrict the number of word ids.  defaults to 10 if not specified.

    list_ids=n,n,n - optional.  restrict the word ids to those in the given lists.

    returns a list of all of the word_ids that match the constraints.  the ids are unique but the order is undefined.

    TODO: sanity check the value of limit
    """

    recent = request.args.get('recent', default='False').lower() == 'true'
    limit = int(request.args.get('limit', default='10'))
    list_ids = request.args.get('list_ids', [])
    if list_ids:
        list_ids = list_ids.split(',')
        list_ids = list(map(lambda x: int(x), list_ids))

        word_ids = get_word_ids_from_list_ids(limit, list_ids, recent)
    else:
        word_ids = get_word_ids(limit, recent)

    result = {
        "word_ids": word_ids
    }
    return jsonify(result)


@app.route('/api/quiz_data', methods=['PUT', 'POST'])
def quiz_data():
    """
    given a quiz key and a list of word_ids, get all of the attribute values quizzed for each of the words.

    although this is invoked with a PUT request, this doesn't actually change the state of the server.  we
    use PUT so that we can have longer list of word ids than we can put into a GET url, so the request is idempotent.

    the word IDs come in as a stringified list of ints:  "[1, 2, 3]"
    """
    if request.method == 'PUT':
        quizkey = request.form.get('quizkey')
        word_ids = request.form.get('word_ids', '[]')
        word_ids = json.loads(word_ids)
        word_ids = list(map(str, word_ids))
        word_ids = ','.join(word_ids)
        result = []
        if word_ids:
            query = quiz_sql.build_quiz_query(quizkey, word_ids)
            with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
        return jsonify(result)

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

    return jsonify('OK')


def get_word_ids(limit, recent):
    query = """
        select w.id word_id from word w
        """
    if recent:
        order_by = " order by w.added desc "
    else:
        order_by = " order by rand() "
    query += order_by
    limit_clause = " limit %s " % limit if limit else ""
    query += limit_clause
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(query)
        query_result = cursor.fetchall()
        return [x['word_id'] for x in query_result]


def get_word_ids_from_list_ids(limit, list_ids, recent):
    """
    returns a list containing 0 or more unique list ids.
    """

    results = []
    for list_id in list_ids:
        # use the API so we don't have to worry about whether any are smart lists
        url = "%s/api/wordlist/%s" % (Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        results.append(result)

    # dig the word_ids out of the list results
    word_ids = []
    for result in results:
        word_ids += [x['word_id'] for x in result['known_words']]

    # remove any duplicates
    word_ids = list(set(word_ids))

    # we'll have to apply the recent and limit filters here in software
    if len(word_ids):
        query = """
            select w.id word_id from word w
            where w.id in (%s)
            """ % (','.join(['%s'] * len(word_ids)))

        if recent:
            order_by = " order by w.added desc "
        else:
            order_by = " order by rand() "

        query += order_by

        limit_clause = " limit %s " % limit if limit else ""

        query += limit_clause

        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            cursor.execute(query, word_ids)

            query_result = cursor.fetchall()

            word_ids = [x['word_id'] for x in query_result]

    return word_ids


@app.route('/healthcheck')
def healthcheck():
    return 'OK'


@app.route('/dbcheck')
def dbcheck():
    # TODO: have to disable mysql server autostart to test no-connection condition
    pass


@app.route('/api/words', methods=['PUT'])
def get_words():
    """
    given a list of word_ids, get the details for each word:  word, attributes, etc.

    the word IDs come in as a stringified list of ints:  "[1, 2, 3]"
    """

    sql = """
    select
        pos_name,
        word,
        word_id,
        attrkey,
        attrvalue value,
        pf.sort_order
    from
        mashup_v
    inner join pos_form pf on pf.attribute_id = mashup_v.attribute_id and 
    pf.pos_id = mashup_v.pos_id
    where word_id in
        (
        select
            word_id
        from
            mashup_v
        where
            word_id in ({word_ids})
        )
    """
    word_ids = request.form.get('word_ids', '[]')
    word_ids = json.loads(word_ids)
    word_ids = list(map(str, word_ids))
    word_ids = ','.join(word_ids)
    result = []
    if word_ids:
        d = {
            "word_ids": word_ids
        }
        query = sql.format(**d)
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            dict_result = {}
            for r in rows:
                if not dict_result.get(r['word_id']):
                    dict_result[r['word_id']] = {}
                dict_result[r['word_id']]['word'] = r['word']
                dict_result[r['word_id']]['word_id'] = r['word_id']
                dict_result[r['word_id']]['pos_name'] = r['pos_name']
                dict_result[r['word_id']][r['attrkey']] = r['value']

            result = list(dict_result.values())

    return jsonify(result)


@app.route('/api/word/<string:word>')
def get_word(word):
    """
    return attributes for every word that matches <word>.  since
    (word, pos_id) is a unique key, it is possible to return more than
    one set of attributes for a given word.  ex: 'braten' is a noun
    and a verb.

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
    attrvalue value,
    pf.sort_order
from
    mashup_v
inner join pos_form pf on pf.attribute_id = mashup_v.attribute_id and 
pf.pos_id = mashup_v.pos_id
where word_id in
    (
    select
        word_id
    from
        mashup_v
    where
        word = %s
    )
order by word_id, pf.sort_order
"""

    partial_match_sql = """
    select
        pos_name,
        word,
        word_id,
        attrkey,
        attrvalue value,
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
            word like %s or attrvalue like %s
        )
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
        dict_result = {}
        for r in rows:
            if not dict_result.get(r['word_id']):
                dict_result[r['word_id']] = {}
            dict_result[r['word_id']]['word'] = r['word']
            dict_result[r['word_id']]['word_id'] = r['word_id']
            dict_result[r['word_id']]['pos_name'] = r['pos_name']
            dict_result[r['word_id']][r['attrkey']] = r['value']

        result = list(dict_result.values())
        # use jsonify even if the result looks like json already.  jsonify ensures that the content type and
        # mime headers are correct.

        return jsonify(result)


@app.route('/list_details/<int:list_id>')
def list_details(list_id):
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
    select
        id, name, source, ifnull(code, '') code
     from wordlist
    where id = %s
    """
        cursor.execute(sql, (list_id,))
        wl_row = cursor.fetchone()

        return render_template('list_details.html', wl_row=wl_row)


@app.route('/api/wordlist', methods=['POST'])
def create_wordlist():
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        name = request.form.get('name')
        source = request.form.get('source')
        code = request.form.get('code')

        if not name:
            raise Exception("can't create list with empty name")

        # this is well-behaved if source and code are not given.

        try:
            cursor.execute('start transaction')

            sql = "insert into wordlist (name, source, code) values (%s, %s, %s)"
            cursor.execute(sql, (name, source, code))
            cursor.execute("select last_insert_id() list_id")
            result = cursor.fetchone()
            dbh.commit()
            return jsonify(result)
        except Exception as e:
            cursor.execute('rollback')
            raise e


@app.route('/api/wordlist/<int:list_id>', methods=['GET', 'PUT', 'DELETE'])
def wordlist_api(list_id):
    if request.method == 'PUT':
        name = request.form.get('name')
        source = request.form.get('source')
        code = request.form.get('code')
        notes = request.form.get('notes')

        if not name:
            raise Exception("can't set list name to be empty string")

        sql = """
        update wordlist
        set name = %(name)s, source = %(source)s, code = %(code)s, notes = %(notes)s
        where id = %(list_id)s"""

        args = {
            'name': name,
            'source': source,
            'code': code,
            'notes': notes,
            'list_id': list_id
        }
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            cursor.execute(sql, args)
            dbh.commit()

        return 'OK'

    if request.method == 'DELETE':
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = "delete from wordlist where id = %s"
            cursor.execute(sql, (list_id,))
            dbh.commit()

        return 'OK'

    # uses WORDLIST_DETAIL_SCHEMA
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            id wordlist_id,
            name,
            source,
            ifnull(notes, '') notes,
            ifnull(code, '') code
        from wordlist
        where id = %s
        """
        cursor.execute(sql, (list_id,))
        wl_row = cursor.fetchone()
        if not wl_row:
            return jsonify({})

        code = wl_row['code'].strip()

        result = dict(wl_row)
        result['source_is_url'] = result['source'].startswith('http') if result['source'] else False
        result['is_smart'] = bool(code)

        if code:
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
            """ % code

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

        return jsonify(result)


@app.route('/wordlist/<int:list_id>')
def wordlist(list_id):
    nchunks = request.args.get('nchunks', app.config['NCHUNKS'], type=int)
    url = "%s/api/wordlist/%s" % (Config.DB_URL, list_id)
    r = requests.get(url)
    result = json.loads(r.text)

    if result['is_smart']:
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


@app.route('/api/wordlists', methods=['GET', 'DELETE'])
def wordlists_api():
    if request.method == 'DELETE':
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

    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
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
select name, id wordlist_id, ifnull(lcount, 0) count, code
from wordlist
left join wordlist_counts wc on wc.wordlist_id = wordlist.id
order by name
        """
        cursor.execute(sql)
        rows = cursor.fetchall()

        # maps list id to list info
        dict_result = {}

        for r in rows:
            # TODO - the connector is returning the count as a string, find out WTF
            r['count'] = int(r['count'])
            dict_result[r['wordlist_id']] = r
            dict_result[r['wordlist_id']]['is_smart'] = bool(r['code'])

            if r['code']:
                cursor.execute(r['code'])
                rows = cursor.fetchall()
                dict_result[r['wordlist_id']]['count'] = len(rows)
                del r['code']

        # json_schema.WORDLIST_DETAIL_SCHEMA
        return jsonify(list(dict_result.values()))


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
        newlist = request.form['name']
        source = request.form['source']
        sql = "insert ignore into wordlist (name, source) values (%s, %s)"
        cursor.execute(sql, (newlist, source))
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
    source = request.form['source']
    code = request.form['code']
    id = request.form['list_id']
    sql = "update wordlist set name = %s, source = %s, code = %s where id = %s"
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        cursor.execute(sql, (name, source, code, id))
        dbh.commit()

    target = url_for('wordlist', list_id=id)
    return redirect(target)


@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    word = request.form['word']
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

        pos_infos = get_data_for_addword_form(cursor, list_id, word=word)

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

    if word_id and word:
        raise Exception("can't have both word_id and word here")

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


def get_data_for_addword_form(cursor, list_id, **kwargs):
    word = kwargs.get('word')
    word_id = kwargs.get('word_id')

    form_dict = get_pos_info_for_form(cursor)

    checked_pos = None
    if word_id:
        word_id = int(word_id)
        # this is harder.  in this case we have an existing word.  we need
        # to fill in all the attribute values for it, for all parts of
        # speech for this word that exist in this word list.

        checked_pos, word = populate_form_dict(cursor, form_dict, word_id=word_id)
    else:
        checked_pos, word = populate_form_dict(cursor, form_dict, word=word)

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
    return pos_infos


@app.route('/add_word')
def add_word():
    """
    display the page to add a word.  word may be in the request, or not.
    """
    with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        word = request.args.get('word')
        word_id = request.args.get('word_id')
        list_id = request.args.get('list_id')

        # if the form contains a word_id, then it is in the word table.
        # if the form does NOT contain a word_id, then that word does not exist
        # in the word table.

        if not word and not word_id:
            raise Exception('word and word_id both missing')

        pos_infos = get_data_for_addword_form(cursor, list_id, word=word, word_id=word_id)

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
        if pos_name == 'Noun':
            word = word.capitalize()

        if not word:
            raise Exception("no word")

        list_id = request.form.get('list_id')
        w_sql = """
    insert ignore into word (pos_id, word)
    values (%s, %s)
    """
        cursor.execute(w_sql, (form_pos_id, word))

        id_sql = "select last_insert_id()"
        cursor.execute(id_sql)
        r = cursor.fetchone()
        word_id = r['last_insert_id()']

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
                value = request.form[k]
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
            target = url_for('add_word')

        return redirect(target)
