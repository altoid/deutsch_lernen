from contextlib import closing
from flask import current_app
from mysql.connector import connect

# no view functions here, just utilities needed by more than one blueprint.


def process_word_query_result(rows):
    """
    take the rows returned by the query in get_words_from_word_ids and morph them into the format specified
    by WORDS_RESPONSE_SCHEMA.
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
        dict_result[r['word_id']]['attributes'].append(attr)
    result = list(dict_result.values())
    return result


def get_words_from_word_ids(word_ids):
    """
    returns word object for every valid word id.  returns empty list if no word_id was found.
    """
    format_args = ['%s'] * len(word_ids)
    format_args = ', '.join(format_args)
    sql = """
    select
        pos_name,
        word,
        word_id,
        attrkey,
        attrvalue,
        sort_order
    from
        mashup_v
    where word_id in (%s)
    order by sort_order
    """ % format_args

    result = []
    if word_ids:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
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
    select word_id
    from wordlist_known_word
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


