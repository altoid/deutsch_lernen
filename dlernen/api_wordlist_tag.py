import mysql.connector.errors
from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js
from contextlib import closing
import jsonschema

# view functions for tags and word/tag linkages in wordlists

bp = Blueprint('api_wordlist_tag', __name__)


@bp.route('/api/wordlist/<int:wordlist_id>/tags', methods=['POST'])
def add_tags(wordlist_id):
    # returns a message and a status code, no object.

    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    new_tags = list(set(payload))  # ensure no redundant tags

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
            if rows:
                if new_tags:
                    args = [(wordlist_id, tag) for tag in new_tags]

                    sql = """
                    insert ignore into wordlist_tag (wordlist_id, tag)
                    values (%s, %s)
                    """
                    cursor.executemany(sql, args)

                cursor.execute('commit')
                return "OK", 200

            cursor.execute('rollback')
            return "list %s not found" % wordlist_id, 404

        except mysql.connector.errors.ProgrammingError as e:
            cursor.execute('rollback')
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/api/wordlist/<int:wordlist_id>/tags', methods=['GET'])
def get_tags(wordlist_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            # the wordlist_id must exist
            sql = """
            select id
            from wordlist
            where id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            if rows:
                sql = """
                select id as wordlist_tag_id, tag
                from wordlist_tag
                where wordlist_id = %s
                order by tag
                """

                cursor.execute(sql, (wordlist_id,))
                rows = cursor.fetchall()

                result = {
                    "wordlist_id": wordlist_id,
                    "tags": rows
                }
                jsonschema.validate(result, js.WORDLIST_TAG_RESPONSE_SCHEMA)

                return result

            return "list %s not found" % wordlist_id, 404

        except mysql.connector.errors.ProgrammingError as e:
            print(e.msg)
            return str(e), 500
        except Exception as e:
            print(e.__class__)
            return str(e), 500


@bp.route('/api/wordlist/<int:wordlist_id>/tags', methods=['PUT'])
def update_tags(wordlist_id):

    # returns a message and a status code, no object.

    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_UPDATE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # checks:
    #
    # - given tag ids exist for this wordlist
    # - no duplicate tag ids

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

            # get all the tag ids.  from the request...
            given_tag_ids = {x['wordlist_tag_id'] for x in payload}

            # and from the database
            sql = """
            select id as wordlist_tag_id
            from wordlist_tag
            where wordlist_id = %s
            """
            cursor.execute(sql, (wordlist_id,))
            rows = cursor.fetchall()
            current_tag_ids = {x['wordlist_tag_id'] for x in rows}

            # if the request contains any tag ids not from this wordlist, request is no good.
            invalid_tag_ids = given_tag_ids - current_tag_ids
            if invalid_tag_ids:
                cursor.execute('rollback')
                message = "invalid tag ids:  %s" % list(invalid_tag_ids)
                return message, 400

            # no dup ids allowed in request.
            given_tag_ids_list = [x['wordlist_tag_id'] for x in payload]

            if len(given_tag_ids) != len(given_tag_ids_list):
                return "can't update tag multiple times in one request", 400

            # checks complete, let's do this

            updates = []
            deletes = []

            for t in payload:
                if 'tag' in t:
                    updates.append(t)
                else:
                    deletes.append(t)

            if deletes:
                delete_sql = """
                delete from wordlist_tag
                where id = %(wordlist_tag_id)s
                """
                args = [
                    {
                        "wordlist_tag_id": x['wordlist_tag_id']
                    } for x in deletes
                ]
                cursor.executemany(delete_sql, args)

            if updates:
                update_sql = """
                update wordlist_tag
                set tag = %(newtag)s
                where id = %(wordlist_tag_id)s and wordlist_id = %(wordlist_id)s
                """
                args = [
                    {
                        "newtag": x['tag'],
                        "wordlist_tag_id": x['wordlist_tag_id'],
                        "wordlist_id": wordlist_id
                    }
                    for x in updates
                ]
                cursor.executemany(update_sql, args)

            cursor.execute('commit')

            return "OK", 200
        except mysql.connector.errors.ProgrammingError as e:
            return str(e), 500
        except Exception as e:
            return str(e), 500


# remove tags from the database
@bp.route('/api/wordlist/<int:wordlist_id>/tags/batch_delete', methods=['PUT'])
def delete_tags(wordlist_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    tags = payload

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

            # if no tags are given then we delete them all!

            if tags:
                sql = """
                delete from wordlist_tag
                where wordlist_id = %(wordlist_id)s
                and tag = %(tag)s
                """

                args = [
                    {
                        "wordlist_id": wordlist_id,
                        "tag": x
                    }
                    for x in tags
                ]

                cursor.executemany(sql, args)
            else:
                sql = """
                delete from wordlist_tag
                where wordlist_id = %(wordlist_id)s
                """
                cursor.execute(sql, {"wordlist_id": wordlist_id})

            cursor.execute('commit')
            return "OK", 200

        except mysql.connector.errors.ProgrammingError as e:
            return str(e), 500
        except Exception as e:
            return str(e), 500


@bp.route('/api/wordlist/<int:wordlist_id>/tag_words', methods=['PUT'])
def tag_words(wordlist_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_WORD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            cursor.execute('commit')

            return "unimplemented", 501
        except mysql.connector.errors.ProgrammingError as e:
            return str(e), 500
        except Exception as e:
            return str(e), 500


@bp.route('/api/wordlist/<int:wordlist_id>/untag_words', methods=['PUT'])
def untag_words(wordlist_id):
    # note:  empty payload means delete all links for this wordlist!
    try:
        payload = request.get_json()
        jsonschema.validate(payload, js.WORDLIST_TAG_WORD_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            cursor.execute('commit')

            return "unimplemented", 501
        except mysql.connector.errors.ProgrammingError as e:
            return str(e), 500
        except Exception as e:
            return str(e), 500
