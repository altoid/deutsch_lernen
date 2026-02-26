import mysql.connector.errors
from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js
from dlernen import common
from contextlib import closing
import jsonschema
import requests

# view functions for tags and word/tag linkages in wordlists

bp = Blueprint('api_wordlist_tag', __name__, url_prefix='/api/wordlist/tags')


@bp.route('/<int:wordlist_id>/<int:word_id>', methods=['GET'])
def get_tags(wordlist_id, word_id):
    # get all the tags affixed to this word id in this wordlist.

    # perform the following checks:
    #
    # - wordlist exists
    # - wordlist is not a smart list
    # - if not a smartlist, word is present in the list.
    #

    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    metadata = r.json()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            result = {
                "wordlist_id": wordlist_id,
                "word_id": word_id,
                "tags": []
            }

            members = set(common.get_word_ids_from_wordlists([wordlist_id], cursor))
            if word_id not in members:
                return "word %s not in list %s" % (word_id, wordlist_id), 404

            if metadata['list_type'] == 'smart':
                # not considered an error condition.
                return result

            # checks complete, let's do this.
            sql = """
            select tag from tag
            where wordlist_id=%(wordlist_id)s and word_id=%(word_id)s
            """

            cursor.execute(sql, {
                "wordlist_id": wordlist_id,
                "word_id": word_id
            })
            rows = cursor.fetchall()

            result['tags'] = [x['tag'] for x in rows]
            jsonschema.validate(result, js.WORD_TAG_RESPONSE_SCHEMA)

            return result, 200

        except mysql.connector.errors.ProgrammingError as e:
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            return str(e), 500


@bp.route('/<int:wordlist_id>', methods=['GET'])
def get_all_tags(wordlist_id):
    # get all the tags across all the words in the wordlist.
    # the response will not indicate with tags go with which word.  it contains just the wordlist id and
    # the list of tags.

    # perform the following checks:
    #
    # - wordlist exists
    # - wordlist is not a smart list
    # - if not a smartlist, word is present in the list.
    #

    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    metadata = r.json()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            result = {
                "wordlist_id": wordlist_id,
                "tags": []
            }

            if metadata['list_type'] == 'smart':
                # not considered an error condition.
                return result

            # checks complete, let's do this.
            sql = """
            select distinct tag from tag
            where wordlist_id=%(wordlist_id)s
            order by tag
            """

            cursor.execute(sql, {
                "wordlist_id": wordlist_id
            })
            rows = cursor.fetchall()

            result['tags'] = [x['tag'] for x in rows]
            jsonschema.validate(result, js.WORD_TAG_RESPONSE_SCHEMA)

            return result, 200

        except mysql.connector.errors.ProgrammingError as e:
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            return str(e), 500


@bp.route('/<int:wordlist_id>/<int:word_id>', methods=['POST'])
def add_tags(wordlist_id, word_id):
    # returns a message and a status code, no object.
    # the payload is just a list of tags.

    # operation is not allowed on smart lists.
    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    metadata = r.json()
    if metadata['list_type'] == 'smart':
        message = "cannot add tags to words in a smart list:  %s" % wordlist_id
        return message, 400

    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    new_tags = list(set(payload))  # ensure no redundant tags
    if not new_tags:
        return "OK", 201

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

            # note that if word_id is not in the wordlist, this insert won't do anything.  the check above
            # keeps this from happening, but without the check nothing bad will happen anyway.
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
            return "OK", 201

        except mysql.connector.errors.ProgrammingError as e:
            cursor.execute('rollback')
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/<string:tag>', methods=['DELETE'])
def delete_tag(tag):
    # delete this tag from the given wordlists, or from every wordlist if no wordlist ids are given.
    # (query parameters in URLs is an acceptable practice)

    wordlist_ids = request.args.getlist('wordlist_id')
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            if wordlist_ids:
                sql = """
                delete from tag
                where tag = %(tag)s
                and wordlist_id = %(wordlist_id)s
                """

                cursor.execute('start transaction')

                cursor.executemany(sql,
                                   [
                                       {'tag': tag, 'wordlist_id': x}
                                       for x in wordlist_ids
                                   ])
                cursor.execute('commit')
                return "OK", 200

            else:
                cursor.execute('start transaction')

                sql = """
                delete from tag
                where tag = %(tag)s
                """

                cursor.execute(sql, {'tag': tag})
                cursor.execute('commit')
                return "OK", 200

        except mysql.connector.errors.ProgrammingError as e:
            cursor.execute('rollback')
            return str(e), 500
        except Exception as e:
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/<int:wordlist_id>/<int:word_id>', methods=['DELETE'])
def delete_tags_for_word_id(wordlist_id, word_id):
    # clear tags from this word id in this wordlist.  tags are given in the URL.  if no tags are given in the URL,
    # do nothing.
    # returns a message and a status code, no object.

    # operation is not allowed on smart lists.
    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    metadata = r.json()
    if metadata['list_type'] == 'smart':
        message = "cannot remove tags from words in a smart list:  %s" % wordlist_id
        return message, 400

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
