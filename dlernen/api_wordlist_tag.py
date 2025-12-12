import mysql.connector.errors
from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js
from contextlib import closing
import jsonschema
import requests

# view functions for tags and word/tag linkages in wordlists
# FIXME currently no unit tests for these

bp = Blueprint('api_wordlist_tag', __name__)


@bp.route('/api/wordlist/<int:wordlist_id>/<int:word_id>/tags', methods=['POST'])
def add_tags(wordlist_id, word_id):
    # returns a message and a status code, no object.

    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    new_tags = list(set(payload))  # ensure no redundant tags
    if not new_tags:
        return "OK", 200

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            # the wordlist_id must exist
            sql = """
            select id
            from wordlist
            where id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "list %s not found" % wordlist_id, 404

            # the word_id must be present in this list
            sql = """
            select wordlist_id, word_id
            from wordlist_known_word
            where wordlist_id=%(wordlist_id)s and word_id=%(word_id)s
            """
            cursor.execute(sql, {
                "wordlist_id": wordlist_id,
                "word_id": word_id
            })
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "word %s not in list %s" % (word_id, wordlist_id), 400

            # checks complete, let's do this.
            sql = """
            insert ignore into tag (wordlist_id, word_id, tag)
            values (%(wordlist_id)s, %(word_id)s, %(tag)s)
            """

            args = [
                {
                    "wordlist_id": wordlist_id,
                    "word_id": word_id,
                    "tag": tag
                }
                for tag in new_tags
            ]
            cursor.executemany(sql, args)

            cursor.execute('commit')
            return "OK", 200

        except mysql.connector.errors.ProgrammingError as e:
            cursor.execute('rollback')
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/api/wordlist/<int:wordlist_id>/<int:word_id>/tags', methods=['DELETE'])
def delete_tags(wordlist_id, word_id):
    # returns a message and a status code, no object.
    doomed_tags = request.args.getlist('tag')

    doomed_tags = list(set(doomed_tags))  # ensure no redundant tags
    if not doomed_tags:
        return "OK", 200

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            # the wordlist_id must exist
            sql = """
            select id
            from wordlist
            where id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "list %s not found" % wordlist_id, 404

            # the word_id must be present in this list
            sql = """
            select wordlist_id, word_id
            from wordlist_known_word
            where wordlist_id=%(wordlist_id)s and word_id=%(word_id)s
            """
            cursor.execute(sql, {
                "wordlist_id": wordlist_id,
                "word_id": word_id
            })
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "word %s not in list %s" % (word_id, wordlist_id), 400

            # checks complete, let's do this.
            sql = """
            delete from tag
            where wordlist_id=%(wordlist_id)s and word_id=%(word_id)s and tag=%(tag)s
            """

            args = [
                {
                    "wordlist_id": wordlist_id,
                    "word_id": word_id,
                    "tag": tag
                }
                for tag in doomed_tags
            ]
            cursor.executemany(sql, args)

            cursor.execute('commit')
            return "OK", 200

        except mysql.connector.errors.ProgrammingError as e:
            cursor.execute('rollback')
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            cursor.execute('rollback')
            return str(e), 500
