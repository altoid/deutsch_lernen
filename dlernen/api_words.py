from flask import Blueprint, request, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js, common
from contextlib import closing
import jsonschema


# view functions for /api/words URLs are here.

bp = Blueprint('api_words', __name__, url_prefix='/api/words')


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
            tag_args = ', '.join(['%s'] * len(tags))
            id_args = ', '.join(['%s'] * len(wordlist_ids))

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
            word_ids = common.get_word_ids_from_wordlists(wordlist_ids, cursor)

        elif tags:
            tag_args = ['%s'] * len(tags)
            tag_args = ', '.join(tag_args)

            sql = """
            select distinct word_id
            from tag
            where tag in (%(tag_args)s)
            """ % {'tag_args': tag_args}

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

    result = common.get_words_from_word_ids(word_ids)

    # NB  the word response does not have any tag info in it.
    jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

    # result may be empty.  the only valid case for a 404 is if a wordlist_id is not found,
    # but we aren't checking for that.

    return result


@bp.route('', methods=['PUT'])
def get_words_from_word_ids():
    # this is for PUT requests because we have to send in the list of words ids as a payload.
    # if we try to put the word_ids into a GET URL, the URL might be too long.
    """
    given a list of word_ids, get the details for each word:  word, attributes, etc.
    """

    payload = request.get_json()

    word_ids = payload.get('word_ids', [])
    result = common.get_words_from_word_ids(word_ids)

    jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

    return result
