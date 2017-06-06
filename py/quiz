#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import quiz_sql
import sys
import codecs
import dsn
import pprint

pp = pprint.PrettyPrinter()
# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = codecs.getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

db = dsn.getConnection()
c = db.cursor()

q = """
select id, name, quizkey
from quiz
where quizkey not in ('genders', 'definitions')
order by id
"""

choices = {}
c.execute(q)
for row in c.fetchall():
    choices[row['id']] = row

for k in choices:
    print k, choices[k]['name']

# pick attributes
qkey = None
while True:
    choice = raw_input('pick attribute, q to quit ---> ').strip()

    if choice == '':
        continue

    if choice == 'q':
        break

    try:
        choice = int(choice)

        if choice in choices.keys():
            qkey = choices[choice]['quizkey']
            break

    except ValueError:
        continue

if not qkey:
    print "no quiz chosen"
    sys.exit()

q = quiz_sql.next_item_query % {'quizkey':qkey}

wordcount = 1
done = False
while not done:
    c.execute(q)
    for row in c.fetchall():
        prompt = "[%s] answer, q to quit --[%s]--> " % (wordcount, row['word'])
        answer = raw_input(prompt)
        answer = unicode(answer, 'utf8').strip().lower()
        while len(answer) == 0:
            answer = raw_input(prompt)
            answer = unicode(answer, 'utf8').strip().lower()
    
        if answer == row['value']:
            print 'ja'
            row['correct_count'] += 1
        elif answer == 'q':
            done = True
            continue
        else:
            print 'nein:  %s' % (row['value'])
    
        row['presentation_count'] += 1
    
        u = """
    insert into quiz_score
    (quiz_id,word_id,attribute_id,presentation_count,correct_count)
    VALUES
    (%s, %s, %s, %s, %s)
    on duplicate key update
    presentation_count = values(presentation_count),
    correct_count = values(correct_count)
    """ % (row['quiz_id'],
           row['word_id'],
           row['attribute_id'],
           row['presentation_count'],
           row['correct_count'])
    
        c.execute(u)
        db.commit()

        wordcount += 1

c.close()
db.close()

print 'auf wiedersehen'
