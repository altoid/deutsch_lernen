#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import common
import noun
import sys
import codecs
import dsn
import argparse

def usage():
    global db
    global c

    keys = get_keys(db, c)
    msg = """
optional attribute keys to populate:
"""
    for k in keys:
        msg += "\t%s\n" % k

    msg += """
when attribute not specified, populate all attributes
"""
    return msg

def get_keys(db, c):
    q = """
 select attribute.attrkey
 from pos, attribute, pos_form
 where pos.id = pos_form.pos_id
   and attribute.id = pos_form.attribute_id
   and pos.name ='verb'
"""

    attrkeys = set()
    c.execute(q)
    for row in c.fetchall():
        r = dict(zip(['attrkey'],
                     row))
        attrkeys.add(r['attrkey'])

    return attrkeys

def check_key(db, c, attrkey):
    keys = get_keys(db, c)
    return attrkey in keys


def jam(db, c, tuples):
    if len(tuples) > 0:
        t = ','.join([x for x in tuples])
        iquery = """
insert into word_attribute(attribute_id, word_id, value) values %s
on duplicate key update value=values(value)
""" % t
        c.execute(iquery)
        db.commit()


# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = codecs.getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

db = dsn.getConnection()
c = db.cursor()
parser = argparse.ArgumentParser(usage=usage())
parser.add_argument("-k", "--key",
                    help="attr key to populate")
args = parser.parse_args()
keyfilter = ""
if args.key:
    attrkey = args.key.strip().lower()
    if not check_key(db, c, attrkey):
        print "no such key:  %s" % attrkey
        sys.exit(1)

    keyfilter = """ and a.attrkey = '%(attrkey)s' """ % {
        'attrkey' : attrkey }

q = """
select a.attrkey, x.attribute_id, x.word_id, w.word
from words_x_attributes_v x 
inner join pos on pos.id = x.pos_id
inner join attribute a on a.id = x.attribute_id
inner join pos_form on pos.id = pos_form.pos_id and a.id = pos_form.attribute_id
inner join word w on w.id = x.word_id
left join word_attribute wa on x.attribute_id = wa.attribute_id 
                           and x.word_id = wa.word_id
where pos.name = 'verb'
%(keyfilter)s
and wa.value is null
order by word, sort_order
""" % {'keyfilter' : keyfilter }

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
