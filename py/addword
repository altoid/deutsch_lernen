#!/usr/bin/python

import MySQLdb
# docs at http://mysql-python.sourceforge.net/MySQLdb.html

import _mysql_exceptions

import common
import noun
import sys
import codecs
import dsn
import logging

logging.basicConfig(level=logging.INFO)

def test_connection(db, c):
    try:
        c.execute("select 1")
    except _mysql_exceptions.OperationalError as e:
        # connection went away, retry
        db = dsn.getConnection()
        c = db.cursor()

    return db, c
    
if __name__ == '__main__':
    # https://pythonhosted.org/kitchen/unicode-frustrations.html
    utf8writer = codecs.getwriter('utf8')
    sys.stdout = utf8writer(sys.stdout)
    
    db = dsn.getConnection()
    c = db.cursor()

    # mysql> select * from pos;
    # +----+-------------+
    # | id | name        |
    # +----+-------------+
    # |  3 | Adjective   |
    # |  4 | Adverb      |
    # |  5 | Conjunction |
    # |  1 | Noun        |
    # |  6 | other       |
    # |  7 | Preposition |
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
        7: 'Preposition',
        8: 'Place name',
        9: 'exit'
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
    
        if 'exit' == menu[choice]:
            break
    
        try:
            db, c = test_connection(db, c)
    
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
