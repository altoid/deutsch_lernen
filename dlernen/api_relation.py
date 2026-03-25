from flask import Blueprint, request, current_app
from pprint import pprint, pformat
from mysql.connector import connect
import mysql.connector.errors
from dlernen import common
from dlernen.dlernen_json_schema import get_validator, \
    RELATION_RESPONSE_SCHEMA, \
    RELATION_PAYLOAD_SCHEMA
from contextlib import closing
import jsonschema

bp = Blueprint('api_relation', __name__, url_prefix='/api/relation')


def relation_exists(relation_id, cursor):
    sql = """
    select id from relation where id = %(relation_id)s
    """

    cursor.execute(sql, {'relation_id': relation_id})
    row = cursor.fetchone()
    return row is not None


def __get_relation(relation_id, cursor):
    sql = """
    select id as relation_id,
        notes,
        description
    from relation
    where id = %(relation_id)s
    """

    cursor.execute(sql, {'relation_id': relation_id})
    row = cursor.fetchone()

    if row:
        sql = """
        select word_id
        from word_id_relation
        where relation_id = %(relation_id)s
        """

        cursor.execute(sql, {'relation_id': relation_id})
        rows = cursor.fetchall()

        word_ids = [x['word_id'] for x in rows]
        words = common.get_displayable_words(word_ids, cursor)
        result = {
            'relation_id': relation_id,
            'notes': row['notes'],
            'description': row['description'],
            'words': words
        }

        get_validator(RELATION_RESPONSE_SCHEMA).validate(result)

        return result

    return {}


@bp.route('/<int:relation_id>')
def get_relation(relation_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            result = __get_relation(relation_id, cursor)
            if not result:
                return "relation %s not found" % relation_id, 404

            return result, 200

        except mysql.connector.errors.ProgrammingError as f:
            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            return str(f), 422
        except Exception as e:
            message = "error:  %s" % (str(e))
            print(message)
            return message, 500


def save_word_ids(relation_id, word_ids, cursor):
    if word_ids:
        args = [
            {
                "relation_id": relation_id,
                "word_id": x
            }
            for x in word_ids
        ]

        sql = """
        insert ignore into word_id_relation (relation_id, word_id) 
        values (%(relation_id)s, %(word_id)s)
        """
        cursor.executemany(sql, args)


@bp.route('', methods=['POST'])
def create_relation():
    try:
        payload = request.get_json()
        get_validator(RELATION_PAYLOAD_SCHEMA).validate(payload)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    word_ids = payload.get('word_ids', [])
    if word_ids:
        word_ids, _ = common.check_word_ids(word_ids)

    # description can have leading/trailing whitespace, but if it's only whitespace, insert it as null.
    description = payload.get('description')
    description_stripped = None
    if description is not None:
        description_stripped = description.strip()
    if not description_stripped:
        description = None

    # same for the notes
    notes = payload.get('notes')
    notes_stripped = None
    if notes is not None:
        notes_stripped = notes.strip()
    if not notes_stripped:
        notes = None

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            sql = """
            insert into relation (description, notes) values (%(description)s, %(notes)s)
            """

            cursor.execute(sql, {'description': description, 'notes': notes})
            cursor.execute("select last_insert_id() relation_id")
            result = cursor.fetchone()
            relation_id = result['relation_id']

            if word_ids:
                save_word_ids(relation_id, word_ids, cursor)

            cursor.execute('commit')

            result = __get_relation(relation_id, cursor)
            return result, 201  # this is already validated and jsonified

        except mysql.connector.errors.ProgrammingError as f:
            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            print(str(f))
            print(cursor.statement)
            cursor.execute('rollback')
            return str(f), 422
        except Exception as e:
            print(str(e))
            print(cursor.statement)
            cursor.execute('rollback')
            return "error, transaction rolled back:  %s" % (str(e)), 500


@bp.route('/<int:relation_id>', methods=['PUT'])
def update_relation(relation_id):
    # any words in the payload are added to the relation.

    try:
        payload = request.get_json()
        get_validator(RELATION_PAYLOAD_SCHEMA).validate(payload)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    word_ids = payload.get('word_ids', [])
    if word_ids:
        word_ids, _ = common.check_word_ids(word_ids)

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            if not relation_exists(relation_id, cursor):
                return "no such relation:  %s" % relation_id, 404

            if 'description' in payload:
                description = payload.get('description')
                description_stripped = None
                if description is not None:
                    description_stripped = description.strip()
                if not description_stripped:
                    description = None

                sql = """
                update relation set description = %(description)s
                where id = %(relation_id)s
                """
                cursor.execute(sql, {'relation_id': relation_id, 'description': description})

            if 'notes' in payload:
                notes = payload.get('notes')
                notes_stripped = None
                if notes is not None:
                    notes_stripped = notes.strip()
                if not notes_stripped:
                    notes = None

                sql = """
                update relation set notes = %(notes)s
                where id = %(relation_id)s
                """
                cursor.execute(sql, {'relation_id': relation_id, 'notes': notes})

            if word_ids:
                save_word_ids(relation_id, word_ids, cursor)

            cursor.execute('commit')

            return __get_relation(relation_id, cursor), 200  # this is already validated and jsonified

        except mysql.connector.errors.ProgrammingError as f:
            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            return str(f), 422
        except Exception as e:
            cursor.execute('rollback')
            return "error, transaction rolled back:  %s" % (str(e)), 500


@bp.route('/<int:relation_id>/batch_delete', methods=['PUT'])
def delete_from_relation(relation_id):
    try:
        payload = request.get_json()
        get_validator(RELATION_PAYLOAD_SCHEMA).validate(payload)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    word_ids = payload.get('word_ids', [])
    if word_ids:
        word_ids, _ = common.check_word_ids(word_ids)

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            if not relation_exists(relation_id, cursor):
                return "no such relation:  %s" % relation_id, 404

            if word_ids:
                sql = """
                delete from word_id_relation
                where relation_id = %(relation_id)s and word_id = %(word_id)s
                """

                args = [
                    {
                        'relation_id': relation_id,
                        'word_id': x
                    }
                    for x in word_ids
                ]
                cursor.executemany(sql, args)

            cursor.execute('commit')

            return __get_relation(relation_id, cursor), 200  # this is already validated and jsonified

        except mysql.connector.errors.ProgrammingError as f:
            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            return str(f), 422
        except Exception as e:
            cursor.execute('rollback')
            return "error, transaction rolled back:  %s" % (str(e)), 500


@bp.route('/<int:relation_id>', methods=['DELETE'])
def delete_relation(relation_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = """
            delete from relation 
            where id = %(relation_id)s
            """

            cursor.execute(sql, {'relation_id': relation_id})
            cursor.execute('commit')

            return "OK", 200

        except mysql.connector.errors.ProgrammingError as f:
            cursor.execute('rollback')

            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            return str(f), 422
        except Exception as e:
            cursor.execute('rollback')
            return "error, transaction rolled back:  %s" % (str(e)), 500


@bp.route('/wordlist/<int:wordlist_id>', methods=['POST'])
def create_relation_from_wordlist(wordlist_id):
    # no json payload needed here
    # make sure the wordlist exists, otherwise 400
    return "unimplemented", 501
