#!/usr/bin/python

import MySQLdb

import quiz_sql
import dsn

# docs at http://mysql-python.sourceforge.net/MySQLdb.html

q = quiz_sql.next_item_query % {'quizkey':'definitions'}

db = dsn.getConnection()

def get_article(db):

    article_cursor = db.cursor()
    article_query = """
 select wa.value 
 from word w, word_attribute wa, attribute a 
 where w.id = wa.word_id 
 and wa.attribute_id = a.id 
 and attrkey = 'article' 
 and word_id = %s
""" % d['word_id']

    article_cursor.execute(article_query)
    article = None
    for r1 in article_cursor.fetchall():
        article = r1[0]
        break

    article_cursor.close()
    return article

c = db.cursor()
done = False
counter = 0
while not done:
    c.execute(q)
    for row in c.fetchall():
        d = dict(zip(['word', 'value',
                      'quiz_id','word_id','attribute_id','presentation_count','correct_count'],
                     row))

        # if the word is a noun, get its article.  if it's not a noun, this query retrieves nothing.
        article = get_article(db)

        counter += 1
        print "[%s]" % counter,

        if article:
            print article,

        print unicode(d['word'])
        prompt = "hit return for answer, q to quit:  --> "
        answer = raw_input(prompt).strip().lower()

        if answer.startswith('q'):
            done = True
            continue

        print d['value']

        prompt = "correct? --> "
        answer = raw_input(prompt).strip().lower()

        while len(answer) == 0:
            answer = raw_input(prompt).strip().lower()

        if answer.startswith('y'):
            d['correct_count'] += 1
    
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

print 'bis bald'
