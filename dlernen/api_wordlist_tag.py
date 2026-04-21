import mysql.connector.errors
from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen.dlernen_json_schema import \
    WORDLIST_TAG_PAYLOAD_SCHEMA, \
    WORD_TAG_RESPONSE_SCHEMA
from dlernen.decorators import js_validate_result, js_validate_payload
from dlernen import common
from contextlib import closing
import requests

# view functions for tags and word/tag linkages in wordlists

bp = Blueprint('api_wordlist_tag', __name__, url_prefix='/api/wordlist/tags')


@js_validate_result(WORD_TAG_RESPONSE_SCHEMA)
def __get_tags(cursor, wordlist_id, word_id):
    result = {
        "wordlist_id": wordlist_id,
        "word_id": word_id,
        "tags": []
    }

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

    return result


@bp.route('/<int:wordlist_id>/<int:word_id>', methods=['GET'])
def get_tags(wordlist_id, word_id):
    # get all the tags affixed to this word id in this wordlist.

    # perform the following checks:
    #
    # - wordlist exists
    # - wordlist is not a smart list
    # - if not a smartlist, word is present in the list.
    #

    url = url_for('api_wordlist.get_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    metadata = r.json()

    result = {
        "wordlist_id": wordlist_id,
        "word_id": word_id,
        "tags": []
    }

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            members = set(common.get_word_ids_from_wordlists([wordlist_id], cursor))
            if word_id not in members:
                return "word %s not in list %s" % (word_id, wordlist_id), 404

            if metadata['list_type'] == 'smart':
                # not considered an error condition.
                return result

            # checks complete, let's do this.
            return __get_tags(cursor, wordlist_id, word_id)

        except mysql.connector.errors.ProgrammingError as e:
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            return str(e), 500


@js_validate_result(WORD_TAG_RESPONSE_SCHEMA)
def __get_all_tags(cursor, wordlist_id):
    sql = """
    select distinct tag from tag
    where wordlist_id=%(wordlist_id)s
    order by tag
    """

    cursor.execute(sql, {
        "wordlist_id": wordlist_id
    })
    rows = cursor.fetchall()

    result = {
        "wordlist_id": wordlist_id,
        'tags': [x['tag'] for x in rows]
    }

    return result


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

    url = url_for('api_wordlist.get_metadata', wordlist_id=wordlist_id, _external=True)
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
            return __get_all_tags(cursor, wordlist_id)

        except mysql.connector.errors.ProgrammingError as e:
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            return str(e), 500


@bp.route('/<int:wordlist_id>', methods=['POST'])
@js_validate_payload(WORDLIST_TAG_PAYLOAD_SCHEMA)
def add_tags(wordlist_id):
    # returns a message and a status code, no object.

    payload = request.get_json()

    # the payload is an array, possibly empty.
    if not payload:
        return 'OK', 201

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            # the wordlist_id must exist
            sql = """
            select id, sqlcode
            from wordlist
            where id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "list %s not found" % wordlist_id, 404

            # operation is not allowed on smart lists.
            if rows[0]['sqlcode']:
                cursor.execute('rollback')
                message = "cannot add tags to words in a smart list:  %s" % wordlist_id
                return message, 400

            # toss any word ids that are not in this list.
            payload_word_ids = [x['word_id'] for x in payload]
            member_word_ids, _ = common.check_word_ids(cursor, payload_word_ids)

            if not member_word_ids:
                cursor.execute('rollback')
                message = "no valid word_ids in payload for list:  %s" % wordlist_id
                return message, 400

            # checks complete, let's do this.

            # construct the argument list.
            args = []
            for i in payload:
                if i['word_id'] in member_word_ids:
                    x = [
                        {
                            "wordlist_id": wordlist_id,
                            "word_id": i['word_id'],
                            "tag": tag
                        }
                        for tag in i['tags']
                    ]
                    args += x

            # note that if word_id is not in the wordlist, this insert won't do anything.  the check above
            # keeps this from happening, but without the check nothing bad will happen anyway.
            sql = """
            insert ignore into tag (wordlist_id, word_id, tag)
            values (%(wordlist_id)s, %(word_id)s, %(tag)s)
            """

            if args:
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
    # delete all tags for the word.
    #
    # returns a message and a status code, no object.

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            # the wordlist_id must exist
            sql = """
            select id, sqlcode
            from wordlist
            where id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('rollback')
                return "list %s not found" % wordlist_id, 404

            # operation is not allowed on smart lists.
            if rows[0]['sqlcode']:
                cursor.execute('rollback')
                message = "cannot remove tags from words in a smart list:  %s" % wordlist_id
                return message, 400

            doomed_tags = request.args.getlist('tag')

            # the word_id must be present in this list
            sql = """
            select wordlist_id, word_id
            from wordlist_word
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
            if doomed_tags:
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
            else:
                # drop all tags for this word.
                sql = """
                delete from tag
                where wordlist_id=%(wordlist_id)s and word_id=%(word_id)s
                """
                cursor.execute(sql, {
                    'wordlist_id': wordlist_id,
                    'word_id': word_id
                })

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
