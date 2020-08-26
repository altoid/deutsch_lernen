from flask import Flask, request, render_template, redirect, url_for
import os
from pprint import pprint
import mysql.connector

app = Flask(__name__)
app.config.from_object(os.environ['CONFIG'])

def get_conn():
    dbh = mysql.connector.connect(
        host=app.config['MYSQL_HOST'], 
        user=app.config['MYSQL_USER'],
        passwd=app.config['MYSQL_PASS'],
        db=app.config['MYSQL_DB'])

    cursor = dbh.cursor(dictionary=True)
    return dbh, cursor


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
        arraysize = ((arraysize + nchunks - 1) / nchunks) * nchunks
        chunksize = arraysize / nchunks

    # add one more increment of chunksize so that our zip array includes
    # the last elements
    chunks = [x for x in xrange(0, arraysize + chunksize, chunksize)]

    z = zip(chunks, chunks[1:])

    result = []
    for x in z:
        result.append(arr[x[0]:x[1]])
    return result


@app.route('/word/<string:word>')
def single_word(word):
    dbh, cursor = get_conn()

    list_id = request.args.get('list_id')
    sql = """
select
pos_name,
word_id,
word,
attribute_id,
attrkey,
ifnull(attrvalue, '') attrvalue
from mashup
where word = %s
order by word_id, sort_order
"""
    cursor.execute(sql, (word,))
    rows = cursor.fetchall()
    dict_result = {}
    for r in rows:
        if not dict_result.get(r['word_id']):
            dict_result[r['word_id']] = []
        dict_result[r['word_id']].append(r)
        
    return render_template('word.html', dict_result=dict_result, list_id=list_id, return_to_list_id=list_id)

@app.route('/word/<int:word_id>')
def single_word_id(word_id):
    dbh, cursor = get_conn()

    list_id = request.args.get('list_id')
    sql = """
select
pos_name,
word_id,
word,
attribute_id,
attrkey,
ifnull(attrvalue, '') attrvalue
from mashup
where word_id = %s
order by word_id, sort_order
"""
    cursor.execute(sql, (word_id,))
    rows = cursor.fetchall()
    dict_result = {}
    for r in rows:
        if not dict_result.get(r['word_id']):
            dict_result[r['word_id']] = []
        dict_result[r['word_id']].append(r)
        
    return render_template('word.html', dict_result=dict_result, list_id=list_id)

@app.route('/list_details/<int:list_id>')
def list_details(list_id):
    dbh, cursor = get_conn()
    sql = """
select * from wordlist
where id = %s
"""
    cursor.execute(sql, (list_id,))
    wl_row = cursor.fetchone()

    return render_template('list_details.html', wl_row=wl_row)

@app.route('/wordlist/<int:list_id>')
def wordlist(list_id):
    dbh, cursor = get_conn()
    sql = """
select
    id,
    name,
    source,
    ifnull(notes, '') notes
from wordlist
where id = %s
"""
    cursor.execute(sql, (list_id,))
    wl_row = cursor.fetchone()

    known_words_sql = """
select
ww.wordlist_id,
m.word list_word,
m.word_id,
ww.added,
m.attrvalue definition,
ifnull(m2.attrvalue, '   ') article
from wordlist_known_word ww
left join mashup m
on ww.word_id = m.word_id
and m.attrkey = 'definition'
left join mashup m2
on ww.word_id = m2.word_id
and m2.attrkey = 'article'
where ww.wordlist_id = %s
order by m.word
"""

    unknown_words_sql = """
select
ww.wordlist_id,
ww.word list_word,
ww.added,
null definition,
'   ' article
from wordlist_unknown_word ww
left join mashup m
on ww.word = m.word
and m.attrkey = 'definition'
left join mashup m2
on ww.word = m2.word
and m2.attrkey = 'article'
where ww.wordlist_id = %s
order by ww.word
"""

    cursor.execute(known_words_sql, (list_id,))
    known_words_rows = cursor.fetchall()

    cursor.execute(unknown_words_sql, (list_id,))
    unknown_words_rows = cursor.fetchall()

    known_words = []
    unknown_words = []
    if len(known_words_rows):
        known_words = chunkify(known_words_rows, nchunks=2)

    if len(unknown_words_rows):
        unknown_words = chunkify(unknown_words_rows, nchunks=2)
        
    source_is_url = False
    if wl_row['source'] and wl_row['source'].startswith('http'):
        source_is_url = True

    return render_template('wordlist.html', wl_row=wl_row,
                           source_is_url=source_is_url,
                           list_id=list_id,
                           known_words=known_words,
                           known_words_count=len(known_words_rows),
                           unknown_words_count=len(unknown_words_rows),
                           unknown_words=unknown_words)

@app.route('/')
@app.route('/wordlists')
def wordlists():
    dbh, cursor = get_conn()
    sql = """
select name, id, ifnull(lcount, 0) listcount
from wordlist
left join
(
    select wordlist_id, sum(c) lcount
    from
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
) b on b.wordlist_id = wordlist.id
order by name
"""
    cursor.execute(sql)
    rows = cursor.fetchall()

    return render_template('wordlists.html', rows=rows)


@app.route('/addlist', methods=['POST'])
def addlist():
    dbh, cursor = get_conn()
    newlist = request.form['name']
    source = request.form['source']
    sql = "insert ignore into wordlist (name, source) values (%s, %s)"
    cursor.execute(sql, (newlist, source))
    dbh.commit()

    return redirect('/wordlists')
    # todo:  error handling for empty list name, list that already exists

@app.route('/deletelist', methods=['POST'])
def deletelist():
    dbh, cursor = get_conn()
    doomed = request.form.getlist('deletelist')
    
    if len(doomed):
        format_list = ['%s'] * len(doomed)
        format_args = ', '.join(format_list)
        sql = "delete from wordlist where id in (%s)" % format_args
        args = [int(x) for x in doomed]
        cursor.execute(sql, args)
        dbh.commit()

    return redirect('/wordlists')

@app.route('/edit_list', methods=['POST'])
def edit_list():
    dbh, cursor = get_conn()
    name = request.form['name']
    source = request.form['source']
    id = request.form['list_id']
    sql = "update wordlist set name = %s, source = %s where id = %s"
    cursor.execute(sql, (name, source, id))
    dbh.commit()

    target = url_for('wordlist', list_id=id)
    return redirect(target)

@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    dbh, cursor = get_conn()
    word = request.form['word']
    list_id = request.form['list_id']

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
    dbh, cursor = get_conn()
    notes = request.form['notes']
    id = request.form['list_id']
    sql = "update wordlist set notes = %s where id = %s"
    cursor.execute(sql, (notes, id))
    dbh.commit()

    target = url_for('wordlist', list_id=id)
    return redirect(target)

@app.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    dbh, cursor = get_conn()

    list_id = request.form['list_id']
    known_deleting = request.form.getlist('known_wordlist')
    
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


@app.route('/edit_word', methods=['POST'])
def edit_word():
    dbh, cursor = get_conn()

    attr_id_keys = [x for x in request.form.keys() if x.endswith('_attrid')]

    tuples = []
    for k in attr_id_keys:
        attrkey = k.replace('_attrid', '')
        v = request.form[attrkey].strip()
        if v:
            tuples.append("%%(word_id)s, %%(%s)s, %%(%s)s" % (k, attrkey))

    form_copy = [(f[0], f[1].capitalize()) if f[0] == 'plural' else (f[0], f[1]) for f in request.form.items()]
    form_copy = dict(form_copy)
    
    sql = """
insert into word_attribute(word_id, attribute_id, value)
values (%s)
on duplicate key update value=values(value)
""" % '), ('.join(tuples)

    cursor.execute(sql, form_copy)
    dbh.commit()

    list_id = request.form.get('list_id')
    target = None
    if list_id:
        target = url_for('wordlist', list_id=list_id)
    else:
        target = url_for('single_word', word=request.form['word'])

    return redirect(target)


def get_pos_info_for_form(cursor):
    """
    get all of the part-of-speech info needed to construct the addword form.
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
from mashup
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
from mashup
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
    for k in form_dict.keys():
        pos_fields = [x for x in form_dict[k].values()]
        l = sorted(pos_fields, cmp=lambda x,y: cmp(x['sort_order'], y['sort_order']))
        pos_info = {
            'pos_id': k,
            'pos_fields': l,
            'pos_name': l[0]['pos_name']
            }
        if checked_pos == k:
            pos_info['checked'] = True
            
        pos_infos.append(pos_info)

    pos_infos = sorted(pos_infos, cmp=lambda x,y: cmp(x['pos_id'], y['pos_id']))
    return pos_infos

@app.route('/add_word')
def add_word():
    """
    display the page to add a word.  word may be in the request, or not.
    """
    dbh, cursor = get_conn()
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

    dbh, cursor = get_conn()
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
    pprint(form_pos_id)
    pprint(r)
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
                       
    # all of the text fields have names of the form <pos_id>-<attribute_id>-<attrkey>.
    # look for all the form fields that start with the pos_id.

    values = []
    placeholders = []
    for k in request.form.keys():
        pprint(k)
        splitkey = k.split('-')
        if len(splitkey) < 3:
            continue
        pos_id, attr_id, attrkey = splitkey[:3]
        if pos_id == form_pos_id and request.form[k]:
            placeholder = "(%s, %s, %s)" # word_id, attr_id, value
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

        pprint(wa_sql)
        pprint(values)
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
