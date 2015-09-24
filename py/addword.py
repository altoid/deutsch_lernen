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

# +----+-------------+
# | id | name        |
# +----+-------------+
# |  3 | Adjective   |
# |  4 | Adverb      |
# |  5 | Conjunction |
# |  1 | Noun        |
# |  6 | other       |
# |  2 | Verb        |
# +----+-------------+

# TODO:  construct the menu from what's in the database.
# have to join with the pos_form table to avoid POS without attributes.

menu = {
    1: 'Noun',
    2: 'Verb',
    3: 'Adjective',
    4: 'Adverb',
    5: 'Conjunction',
    6: 'other',
    7: 'exit'
}

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

    if choice == 7:
        break

    if choice == 1:
        done = noun.prompt_noun(db, c)
    else:
        done = common.prompt_word(db, c, menu[choice])

print 'auf wiedersehen'
    
c.close()

db.close()
