#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import quiz_sql
import sys
import codecs
import re
import dsn

# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = codecs.getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

db = dsn.getConnection()

# pick part of speech
c = db.cursor()
c.execute("set @x := 0")
choices = {}

q = """
 select @x := @x + 1 choice, 
 pos.name pos_name, a.attrkey,
 pos.id pos_id, a.id attribute_id
 from pos, attribute a, pos_form
 where pos.id = pos_form.pos_id
 and pos_form.attribute_id = a.id
 order by pos.name, attrkey
"""

c.execute(q)
for row in c.fetchall():
    choices[row['choice']] = row

for k in choices:
    print k, choices[k]['pos_name'], choices[k]['attrkey']

attrs = set()

# pick attributes
while True:
    choice = raw_input('pick attribute, empty when done ---> ').strip()

    if choice == '':
        break

    try:
        choice = int(choice)

        if choice in choices.keys():
            attrs.add(choice)
        else:
            print 'boo'

    except ValueError:
        continue

if len(attrs) == 0:
    print 'no choices, exiting'
    sys.exit()
    
# choose quiz name

# choose quiz key (enforce no spaces)
## quiz key must be unique

# get all the quiz keys
quizkeys = set()

q = """
 select quizkey from quiz
"""

c.execute(q)
for row in c.fetchall():
    quizkeys.add(row[0])

while True:
    qkey  = raw_input('db key for quiz ---> ').strip()

    if qkey == '':
        continue

    if qkey in quizkeys:
        print 'that key exists'
        continue

    qkey = db.escape_string(qkey)
    break

while True:
    qname = raw_input('name of your quiz ---> ').strip()

    if qname == '':
        continue

    qname = db.escape_string(qname);
    break

# stuff db

q = """
 insert into quiz (name, quizkey) values ('%(name)s', '%(quizkey)s')
""" % { 'name':qname,
        'quizkey':qkey }

c.execute(q)

quiz_id = db.insert_id()

vlist = ''

for a in attrs:
    vlist += ',(%(quiz_id)s, %(pos_id)s, %(attr_id)s)' % {
        'quiz_id' : quiz_id,
        'pos_id' : choices[a]['pos_id'],
        'attr_id' : choices[a]['attribute_id']
        }

vlist = vlist[1:]

q = "insert into quiz_structure(quiz_id, pos_id, attribute_id) values " + vlist
c.execute(q)
    
db.commit()
