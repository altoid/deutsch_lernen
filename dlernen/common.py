from contextlib import closing
from flask import current_app
from mysql.connector import connect
from dlernen.decorators import js_validate_result
from dlernen.dlernen_json_schema import ARRAY_WORD_RESPONSE_SCHEMA, \
    ARRAY_DISPLAYABLE_WORD_SCHEMA, \
    ARRAY_WORDLIST_METADATA_RESPONSE_SCHEMA


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


@js_validate_result(ARRAY_DISPLAYABLE_WORD_SCHEMA)
def get_displayable_words(cursor, word_ids):
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

        word_data = {(r['word'], r['word_id']):
            {
                'article': r['article'],
                'definition': r['definition'],
                'word': r['word'],
                'word_id': r['word_id'],
                'pos_name': r['pos_name'],
                'tags': []
            }
            for r in rows
        }

        result = list(word_data.values())

    return result


@js_validate_result(ARRAY_WORD_RESPONSE_SCHEMA)
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


@js_validate_result(ARRAY_WORDLIST_METADATA_RESPONSE_SCHEMA)
def get_wordlist_metadata(cursor, wordlist_ids):
    # empty wordlist_ids means GET ALL

    sql = """
        with wordlist_counts as
        (
            select wordlist_id, sum(c) lcount from
            (
                select wordlist_id, count(*) c
                from wordlist_word
                group by wordlist_id
            ) a
            group by wordlist_id
        )
        select name, id wordlist_id, ifnull(lcount, 0) count, sqlcode, citation
        from wordlist
        left join wordlist_counts wc on wc.wordlist_id = wordlist.id
        """

    if wordlist_ids:
        sql = sql + """
        where wordlist.id in (%(args)s)
        """ % {'args': ','.join(['%s'] * len(wordlist_ids))}

    cursor.execute(sql, wordlist_ids)
    metadata_rows = cursor.fetchall()

    if not metadata_rows:
        return []

    # the connector is returning the count as a Decimal, have to convert it to int
    for r in metadata_rows:
        r['count'] = int(r['count'])

    smartlists = list(filter(lambda x: x['sqlcode'] is not None, metadata_rows))

    # construct a single sql query from all of the sqlcodes, which will give the word counts by wordlist_id
    # as fetched by the sqlcodes.  the query will look like this:
    #
    # sql = """
    # with omg as (
    # select 666 wordlist_id, word_id from
    # (
    # <sqlcode for wordlist 666>
    # ) a666
    # UNION
    # select 555 wordlist_id, word_id from
    # (
    # <sqlcode for wordlist 555>
    # ) a555
    # UNION ...
    # )
    # select wordlist_id, count(*) count
    # from omg
    # group by wordlist_id
    # """

    wordlist_id_to_metadata = {x['wordlist_id']: x for x in metadata_rows}

    if smartlists:
        selectors = [
            """
            select %(wordlist_id)s wordlist_id, word_id from (
            %(sqlcode)s
            ) a%(wordlist_id)s 
            """ % {
                'wordlist_id': x['wordlist_id'],
                'sqlcode': x['sqlcode']
            }
            for x in smartlists
        ]

        sql = ' UNION '.join(selectors)
        sql = """
            with omg as
            (
            %(sql)s
            )
            select wordlist_id, count(*) listcount
            from omg
            group by wordlist_id
            """ % {'sql': sql}

        cursor.execute(sql)
        smartlist_counts = cursor.fetchall()

        for x in smartlist_counts:
            wordlist_id_to_metadata[x['wordlist_id']]['count'] = x['listcount']

    result = list(wordlist_id_to_metadata.values())
    for r in result:
        if r['sqlcode']:
            r['list_type'] = 'smart'
        elif r['count'] > 0:
            r['list_type'] = 'standard'
        else:
            r['list_type'] = 'empty'

    return result


