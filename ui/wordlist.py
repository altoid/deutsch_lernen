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

@app.route('/wordlist')
def wordlist():
    dbh, cursor = get_conn()
    sql = "select name from wordlist"
    cursor.execute(sql)
    rows = cursor.fetchall()

    return render_template('wordlist.html', rows=rows)

@app.route('/addlist', methods=['POST'])
def addlist():
    dbh, cursor = get_conn()
    newlist = request.form['name']
    sql = "insert ignore into wordlist (name) values (%s)"
    cursor.execute(sql, (newlist,))
    dbh.commit()

    return redirect('/wordlist')
    # todo:  error handling for empty list name, list that already exists
