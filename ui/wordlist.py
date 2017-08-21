from flask import Flask, request, render_template, redirect, url_for
import MySQLdb
import MySQLdb.cursors
import os
import pprint

app = Flask(__name__)
app.config.from_object(os.environ['CONFIG'])
pp = pprint.PrettyPrinter()

def get_conn():
    dbh = MySQLdb.connect(
        host=app.config['MYSQL_HOST'], 
        user=app.config['MYSQL_USER'],
        passwd=app.config['MYSQL_PASS'],
        db=app.config['MYSQL_DB'],
        cursorclass=MySQLdb.cursors.DictCursor)

    cursor = dbh.cursor()
    return dbh, cursor

@app.route('/')
def default_route():
    return render_template('index.html')

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
        
    return render_template('word.html', dict_result=dict_result, list_id=list_id)

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

@app.route('/wordlist/<int:list_id>')
def wordlist(list_id):
    dbh, cursor = get_conn()
    sql = """
select * from wordlist
where id = %s
"""
    cursor.execute(sql, (list_id,))
    wl_row = cursor.fetchone()

    # join this wordlist with the mashup view
    sql = """
select distinct
ww.wordlist_id,
ww.word list_word,
ww.added,
m.attrvalue definition,
m.word dict_word
from wordlist_word ww
left join mashup m
on ww.word = m.word
and attrkey = 'definition'
where ww.wordlist_id = %s
order by ww.word
"""

    cursor.execute(sql, (list_id,))
    rows = cursor.fetchall()

    known_words = []
    unknown_words = []
    if len(rows):
        known_words = [x for x in rows if x['dict_word']]
        unknown_words = [x for x in rows if not x['dict_word']]

    source_is_url = False
    if wl_row['source'] and wl_row['source'].startswith('http'):
        source_is_url = True

    return render_template('wordlist.html', wl_row=wl_row,
                           source_is_url=source_is_url,
                           list_id=list_id,
                           known_words=known_words,
                           unknown_words=unknown_words)
                           

@app.route('/wordlists')
def wordlists():
    dbh, cursor = get_conn()
    sql = "select name, id from wordlist"
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

@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    dbh, cursor = get_conn()
    word = request.form['word']
    id = request.form['list_id']
    sql = "insert ignore into wordlist_word (wordlist_id, word) values (%s, %s)"
    cursor.execute(sql, (id, word))
    dbh.commit()

    target = url_for('wordlist', list_id=id)
    return redirect(target)
    # todo:  validate input: word in not bad script, list id is int

@app.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    dbh, cursor = get_conn()

    id = request.form['list_id']
    doomed = request.form.getlist('wordlist')
    
    if len(doomed):
        format_list = ['%s'] * len(doomed)
        format_args = ', '.join(format_list)

        sql = """
delete from wordlist_word
where wordlist_id = %%s
and word in (%s)
""" % format_args

        args = [id] + doomed
        cursor.execute(sql, args)
        dbh.commit()

    target = url_for('wordlist', list_id=id)
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

    sql = """
insert into word_attribute(word_id, attribute_id, value)
values (%s)
on duplicate key update value=values(value)
""" % '), ('.join(tuples)

    cursor.execute(sql, request.form)
    dbh.commit()

    target = url_for('single_word', word=request.form['word'])
    return redirect(target)

@app.route('/add_word')
def add_word():
    """
    display the page to add a word.  word may be in the request, or not.
    """
    dbh, cursor = get_conn()
    word = request.args.get('word')
    list_id = request.args.get('list_id')

    sql = """
select
    p.id pos_id,
    p.name pos_name,
    a.id attribute_id,
    a.attrkey
from
		pos p
inner join pos_form pf on pf.pos_id = p.id
inner join attribute a on a.id = pf.attribute_id
order by p.id, sort_order
"""

    cursor.execute(sql)
    pos_list = cursor.fetchall()

    # create a dict keyed on pos.name

    pos_dict = {}
    for pos in pos_list:
        if not pos_dict.get(pos['pos_name']):
            pos_dict[pos['pos_name']] = []
        pos_dict[pos['pos_name']].append(pos)

    return render_template('addword.html',
                           word=word,
                           list_id=list_id,
                           pos_dict=pos_dict)

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
    word = request.form['word'].strip()
    if not word:
        raise Exception("no word")

    list_id = request.form.get('list_id')
    w_sql = """
insert into word (pos_id, word)
values (%s, %s)
"""
    cursor.execute(w_sql, (form_pos_id, word))

    id_sql = "select last_insert_id()"
    cursor.execute(id_sql)
    r = cursor.fetchone()
    word_id = r['last_insert_id()']

    # all of the text fields have names of the form <pos_id>_<attribute_id>_<attrkey>.
    # look for all the form fields that start with the pos_id.

    values = []
    placeholders = []
    for k in request.form.keys():
        splitkey = k.split('-')
        if len(splitkey) < 3:
            continue
        pos_id, attr_id, attrkey = splitkey[:3]
        if pos_id == form_pos_id and request.form[k]:
            placeholder = "(%s, %s, %s)" # word_id, attr_id, value
            placeholders.append(placeholder)
            values += [word_id, attr_id, request.form[k]]

    if len(values) > 0:
        wa_sql = """
insert into word_attribute (word_id, attribute_id, value)
values
%s
""" % ', '.join(placeholders)

    cursor.execute(wa_sql, values)
    dbh.commit()

    target = url_for('single_word_id', word_id=word_id, list_id=list_id)
    return redirect(target)
