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
    # TODO - currently no unit tests for this.  do we need any?

    wordlist_ids = request.args.getlist('wordlist_id')
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if wordlist_ids:
            word_ids = common.get_word_ids_from_wordlists(wordlist_ids, cursor)
        else:
            sql = """
            select id as word_id from word
            """

            cursor.execute(sql)
            rows = cursor.fetchall()

            word_ids = list(map(lambda x: x['word_id'], rows))

    result = common.get_words_from_word_ids(word_ids)

    jsonschema.validate(result, js.WORDS_RESPONSE_SCHEMA)

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
