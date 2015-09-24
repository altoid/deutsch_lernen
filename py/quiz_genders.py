#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import quiz_sql
import sys
import codecs
import dsn

# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = codecs.getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

q = quiz_sql.next_item_query % {'quizkey':'genders'}

db = dsn.getConnection()
c = db.cursor()

done = False
while not done:
    c.execute(q)
    for row in c.fetchall():
        d = dict(zip(['word', 'value',
                      'quiz_id','word_id','attribute_id','presentation_count','correct_count'],
                     row))
    
        prompt = "answer, q to quit --[%s]--> " % d['word']
        answer = raw_input(prompt).strip().lower()
        while len(answer) == 0:
            answer = raw_input(prompt).strip().lower()
    
        if answer == d['value']:
            print 'ja'
            d['correct_count'] += 1
        elif answer == 'q':
            done = True
            continue
        else:
            print 'nein:  %s %s' % (d['value'], d['word'])
    
        d['presentation_count'] += 1
    
        u = """
    insert into quiz_score
    (quiz_id,word_id,attribute_id,presentation_count,correct_count)
    VALUES
    (%s, %s, %s, %s, %s)
    on duplicate key update
    presentation_count = values(presentation_count),
    correct_count = values(correct_count)
    """ % (d['quiz_id'],
           d['word_id'],
           d['attribute_id'],
           d['presentation_count'],
           d['correct_count'])
    
        c.execute(u)
        db.commit()
        
c.close()
db.close()

print 'auf wiedersehen'
