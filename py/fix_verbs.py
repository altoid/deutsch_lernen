#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import common
import noun
import sys
import codecs
import dsn

# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = codecs.getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

db = dsn.getConnection()
c = db.cursor()

def jam(db, c, tuples):
    if len(tuples) > 0:
        t = ','.join([x for x in tuples])
        iquery = """
insert into word_attribute(attribute_id, word_id, value) values %s
on duplicate key update value=values(value)
""" % t
        c.execute(iquery)
        db.commit()

# TODO:  make this more generic

attrkeys = [
    'third_person_past',
#    'past_participle',
#    'first_person_singular',
#    'second_person_singular',
#    'third_person_singular',
#    'first_person_plural',
#    'second_person_plural',
#    'third_person_plural',
]

q = """

select a.attrkey, x.attribute_id, x.word_id, w.word
from words_x_attributes_v x 
inner join pos on pos.id = x.pos_id
inner join attribute a on a.id = x.attribute_id
inner join word w on w.id = x.word_id
left join word_attribute wa on x.attribute_id = wa.attribute_id 
                           and x.word_id = wa.word_id
where pos.name = 'verb'
and a.attrkey in ( %(attrlist)s )
and wa.value is null
order by x.word_id, field( attrkey, %(attrlist)s )
""" % {'attrlist' : ','.join(["'" + x + "'" for x in attrkeys]) }


c.execute(q)
rowcount = c.rowcount
word_id = None
tuples = []

print "enter 'xxx' to terminate"

for row in c.fetchall():

    r = dict(zip(['attrkey', 'attribute_id', 'word_id', 'word'],
                 row))

    if r['word_id'] != word_id:
        if word_id is not None:
            jam(db, c, tuples)
            tuples = []
        word_id = r['word_id']

    prompt = "--[%03d][%s, %s]--> " % (rowcount, r['word'], r['attrkey'])
    v = raw_input(prompt)
    v = unicode(v, 'utf8').strip().lower()
    if len(v) > 0:
        if (v == 'xxx'):
            break

        tuple = "(%s, %s, '%s')" % (r['attribute_id'], word_id, v)
        tuples.append(tuple)
        rowcount -= 1

jam(db, c, tuples)

print "bis bald"
