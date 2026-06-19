from flask import Blueprint, request, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import common
from contextlib import closing


# view functions for /api/words URLs are here.

bp = Blueprint('api_words', __name__, url_prefix='/api/words')


@bp.route('/incomplete')
def get_incomplete_words():
    # get all of the words for which at least one attribute is not set.  we can pass these to an editing utility.
    wordlist_ids = request.args.getlist('wordlist_id')
    wordlist_ids = list(set(wordlist_ids))  # remove dups

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select distinct word_id
        from mashup_v
        where attrvalue is null
        """

        cursor.execute(sql)
        rows = cursor.fetchall()
        word_ids = [x['word_id'] for x in rows]

        if wordlist_ids and word_ids:
            sql = """
            select distinct word_id
            from wordlist_word
            where wordlist_id in (%(WORDLIST_ID_PLACEHOLDER)s)
            and word_id in (%(WORD_ID_PLACEHOLDER)s)
            """ % {
                'WORD_ID_PLACEHOLDER': common.placeholder_string(word_ids),
                'WORDLIST_ID_PLACEHOLDER': common.placeholder_string(wordlist_ids)
            }
            cursor.execute(sql, wordlist_ids + word_ids)
            rows = cursor.fetchall()
            word_ids = [x['word_id'] for x in rows]

        result = common.get_words_from_word_ids(cursor, word_ids)

        return result


@bp.route('', methods=['GET'])
def get_words():
    """
    given a list of wordlist ids, get all the words in those lists.  if no word list ids are given, dump
    the whole dictionary.
    """

    # NB there is no check for invalid wordlist_id.  i'm tired.

    wordlist_ids = request.args.getlist('wordlist_id')
    tags = request.args.getlist('tag')
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if wordlist_ids and tags:
            tag_args = common.placeholder_string(tags)
            id_args = common.placeholder_string(wordlist_ids)

            sql = """
            select distinct word_id
            from tag
            where tag in (%(tag_args)s)
            and wordlist_id in (%(id_args)s)
            """ % {
                'tag_args': tag_args,
                'id_args': id_args
            }

            cursor.execute(sql, tags + wordlist_ids)
            rows = cursor.fetchall()

            word_ids = list(map(lambda x: x['word_id'], rows))

        elif wordlist_ids:
            word_ids = common.get_word_ids_from_wordlists(cursor, wordlist_ids)

        elif tags:
            sql = """
            select distinct word_id
            from tag
            where tag in (%(tag_args)s)
            """ % {'tag_args': common.placeholder_string(tags)}

            cursor.execute(sql, tags)
            rows = cursor.fetchall()

            word_ids = list(map(lambda x: x['word_id'], rows))

        else:
            sql = """
            select id as word_id from word
            """

            cursor.execute(sql)
            rows = cursor.fetchall()

            word_ids = list(map(lambda x: x['word_id'], rows))

        result = common.get_words_from_word_ids(cursor, word_ids)

        # NB  the word response does not have any tag info in it.
        # common.get_words_from_word_ids validates its return value so we don't need to validate here.

        # result may be empty.  the only valid case for a 404 is if a wordlist_id is not found,
        # but we aren't checking for that.

        return result


@bp.route('', methods=['PUT'])
def get_words_from_word_ids():
    # this is for PUT requests because we have to send in the list of words ids as a payload.
    # if we try to put the word_ids into a GET URL, the URL might be too long.
    """
    disgorges a list of WORD_RESPONSE_SCHEMA objects.
    """

    payload = request.get_json()

    word_ids = payload.get('word_ids', [])
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # common.get_words_from_word_ids validates its return value so we don't need to validate here.

        return common.get_words_from_word_ids(cursor, word_ids)


@bp.route('/displayable/<string:word>')
def get_displayable_words(word):
    # get all the ids for this word

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select id word_id
        from word
        where word = %s
        """

        cursor.execute(sql, (word,))
        rows = cursor.fetchall()
        word_ids = [x['word_id'] for x in rows]

        return common.get_displayable_words(cursor, word_ids)
