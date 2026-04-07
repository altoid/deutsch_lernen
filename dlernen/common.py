from contextlib import closing
from flask import current_app
from mysql.connector import connect
from dlernen.decorators import js_validate_result
from dlernen.dlernen_json_schema import WORD_ARRAY_RESPONSE_SCHEMA

# no view functions here, just utilities needed by more than one blueprint.


# returns two lists:  the word_ids that exist in the database and those that don't.
# it is guaranteed that:
#
# - the lists are disjoint
# - no word id appears more than once in either list.
def check_word_ids(word_ids):
    if not word_ids:
        return [], []

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        id_args = ', '.join(['%s'] * len(word_ids))
        sql = """
        select distinct id word_id
        from word
        where id in (%(id_args)s)
        """ % {'id_args': id_args}

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()
        known_ids = {x['word_id'] for x in rows}
        unknown_ids = set(word_ids) - known_ids

        return list(known_ids), list(unknown_ids)


def process_word_query_result(rows):
    """
    take the rows returned by the query in get_words_from_word_ids and morph them into the format specified
    by WORD_RESPONSE_SCHEMA.
    """
    dict_result = {}
    for r in rows:
        if not dict_result.get(r['word_id']):
            dict_result[r['word_id']] = {}
            dict_result[r['word_id']]['attributes'] = []
        attr = {
            "attrkey": r['attrkey'],
            "attrvalue": r['attrvalue'],
            "sort_order": r['sort_order']
        }
        dict_result[r['word_id']]['word'] = r['word']
        dict_result[r['word_id']]['word_id'] = r['word_id']
        dict_result[r['word_id']]['pos_name'] = r['pos_name']
        dict_result[r['word_id']]['notes'] = r['notes']
        dict_result[r['word_id']]['attributes'].append(attr)
    result = list(dict_result.values())
    return result


def get_displayable_words(word_ids, cursor):
    # for each in a list of word_ids, get the word info needed in order to display each word in a page:
    # definition, article (if noun), and the word itself.  the data structures must pass validation with
    # DISPLAYABLE_WORD_SCHEMA, though it is up to the caller to do the validation.

    result = []
    if word_ids:
        word_ids = list(set(word_ids))  # remove dups

        args = ','.join(['%s'] * len(word_ids))

        sql = """
        select
            m1.word word,
            m1.pos_name pos_name,
            m0.word_id,
            m1.attrvalue definition,
            ifnull(m2.attrvalue, '') article
        from  mashup_v m0
        left  join mashup_v m1
        on    m0.word_id = m1.word_id
        and   m1.attrkey = 'definition'
        left  join mashup_v m2
        on    m0.word_id = m2.word_id
        and   m2.attrkey = 'article'
        where m1.word_id in (%(args)s)
        order by m1.word        
        """ % {'args': args}

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()

        word_data = {(r['word'], r['word_id']): {
            'article': r['article'],
            'definition': r['definition'],
            'word': r['word'],
            'word_id': r['word_id'],
            'pos_name': r['pos_name'],
            'tags': []
        }
            for r in rows}

        result = list(word_data.values())

    return result


@js_validate_result(WORD_ARRAY_RESPONSE_SCHEMA)
def get_words_from_word_ids(word_ids, cursor):
    """
    returns word object for every valid word id.  returns empty list if no word_id was found.
    """
    result = []
    if word_ids:
        format_args = ', '.join(['%s'] * len(word_ids))
        sql = """
        select
            pos_name,
            word,
            word_id,
            attrkey,
            attrvalue,
            notes,
            sort_order
        from
            mashup_v
        where word_id in (%s)
        order by sort_order
        """ % format_args

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()
        result = process_word_query_result(rows)

    return result


# helper function.  returns a list of all of the word_ids in the given wordlists.  works for
# standard and for smart lists.  since we are using UNION and not UNION ALL, there will be no dups
# in the result.
#
# this should be called from within a context manager, e.g.
#
# with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
#     get_word_ids_from_wordlists(wordlist_ids, cursor)
#
def get_word_ids_from_wordlists(wordlist_ids, cursor):
    if not wordlist_ids:
        return []

    wordlist_args = ['%s'] * len(wordlist_ids)
    wordlist_args = ', '.join(wordlist_args)

    sql_for_standard_lists = [
        """
    select distinct word_id
    from wordlist_word
    where wordlist_id in (""" + wordlist_args + """)
    """
    ]

    # make a UNION out of this and all the sqlcode routines for all the word lists
    sql = """
    select sqlcode
    from wordlist
    where id in (""" + wordlist_args + """)
    and sqlcode is not NULL
    """

    cursor.execute(sql, wordlist_ids)
    rows = cursor.fetchall()

    smartlist_clauses = list(map(lambda x: x['sqlcode'], rows))

    sql = ') UNION ('.join(sql_for_standard_lists + smartlist_clauses)
    sql = '( %s )' % sql

    cursor.execute(sql, (*wordlist_ids,))

    rows = cursor.fetchall()

    result = list(map(lambda x: x['word_id'], rows))

    return result
