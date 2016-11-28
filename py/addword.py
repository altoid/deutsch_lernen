#!/usr/local/bin/python
# -*- encoding: utf-8 -*-

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import _mysql_exceptions

import common
import noun
import sys
#import codecs
from kitchen.text.converters import getwriter
import dsn
import logging

logging.basicConfig(level=logging.INFO)

# https://pythonhosted.org/kitchen/unicode-frustrations.html
utf8writer = getwriter('utf8')
sys.stdout = utf8writer(sys.stdout)

print 'fück'
print u'fück'

db = dsn.getConnection()
c = db.cursor()

query = """
 select id, name from pos
 order by id
"""

menu = {}
c.execute(query)
for row in c.fetchall():
    menu[row[0]] = row[1]

query = """
 select max(id) + 1 from pos
"""

c.execute(query)
for row in c.fetchall():
    menu[row[0]] = 'exit'

done = False

while not done:

    for k, v in menu.iteritems():
        print k, v

    while True:
        choice = raw_input('---> ').strip()

        try:
            choice = int(choice)
        except ValueError:
            continue

        if choice in menu.keys():
            break

    if 'exit' == menu[choice]:
        break

    try:
        if menu[choice] == 'Noun':
            done = noun.prompt_noun(db, c)
        else:
            done = common.prompt_word(db, c, menu[choice])
    except _mysql_exceptions.OperationalError as e:
        # connection went away, retry
        db = dsn.getConnection()
        c = db.cursor()
        print "########## database connection timed out, please reenter:"
        if menu[choice] == 'Noun':
            done = noun.prompt_noun(db, c)
        else:
            done = common.prompt_word(db, c, menu[choice])

print 'auf wiedersehen'
    
c.close()
db.close()
