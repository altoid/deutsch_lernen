from contextlib import closing
from flask import current_app
from mysql.connector import connect

# no view functions here, just utilities needed by more than one blueprint.


def get_word_ids_from_wordlists(wordlist_ids):
    """
    helper function.  returns a list of all of the word_ids in the given wordlists.  works for
    standard and for smart lists.
    """

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
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select sqlcode
        from wordlist
        where id in (""" + wordlist_args + """)
        and sqlcode is not NULL
        """

        cursor.execute(sql, (*wordlist_ids,))
        rows = cursor.fetchall()

        smartlist_clauses = list(map(lambda x: x['sqlcode'], rows))

        sql = ' UNION '.join(sql_for_standard_lists + smartlist_clauses)

        cursor.execute(sql, (*wordlist_ids,))

        rows = cursor.fetchall()

        result = list(map(lambda x: x['word_id'], rows))

        return result


