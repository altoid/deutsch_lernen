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

    sql = """
select * from mashup
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
        
    return render_template('word.html', dict_result=dict_result)

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
m.word dict_word
from wordlist_word ww
left join mashup m
on ww.word = m.word
where ww.wordlist_id = %s
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
                           known_words=known_words,
                           unknown_words=unknown_words)
                           

@app.route('/wordlist')
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

    return redirect('/wordlist')
    # todo:  error handling for empty list name, list that already exists

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

@app.route('/edit_word', methods=['POST'])
def edit_word():
    dbh, cursor = get_conn()

    conjunction = []
    for k in request.form.keys():
        if k in ['word', 'word_id']:
            continue

        conjunction.append('%(attrkey)s = %%(%(attrkey)s)s' % {
                'attrkey' : k })

    sql = """
update mashup
set %(conjunction)s
where word_id = %%(word_id)s
""" % {
        'conjunction' : ' and '.join(conjunction)
        }

    print sql

    target = url_for('single_word', word=request.form['word'])
    return redirect(target)
