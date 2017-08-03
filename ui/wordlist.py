from flask import Flask, request, render_template, redirect, url_for
import MySQLdb
import MySQLdb.cursors
import os

app = Flask(__name__)
app.config.from_object(os.environ['CONFIG'])

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

@app.route('/wordlist/<int:list_id>')
def wordlist(list_id):
    dbh, cursor = get_conn()
    sql = """
select * from wordlist
where id = %s
"""
    cursor.execute(sql, (list_id,))
    row = cursor.fetchone()

    return render_template('wordlist.html', row=row)

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
