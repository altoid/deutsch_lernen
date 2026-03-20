from flask import Blueprint, request, current_app, url_for
import requests
from pprint import pprint, pformat
from mysql.connector import connect
from dlernen import common
from dlernen.dlernen_json_schema import get_validator, \
    RELATION_RESPONSE_SCHEMA, \
    RELATION_PAYLOAD_SCHEMA
from contextlib import closing
import jsonschema

bp = Blueprint('api_relation', __name__, url_prefix='/api/relation')


def verify_word_ids(word_ids, cursor):
    # returns two lists:  the word_ids that exist in the database and those that don't.
    # it is guaranteed that:
    #
    # - the lists are disjoint
    # - no word id appears more than once in either list.
    return [], []


@bp.route('/<int:relation_id>')
def get_relation(relation_id):
    return "unimplemented", 501


@bp.route('', methods=['POST'])
def create_relation():
    try:
        payload = request.get_json()
        get_validator(RELATION_PAYLOAD_SCHEMA).validate(payload)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400
    except Exception as e:
        return "bad payload: %s" % str(e), 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')

            if notes is not None and not notes.strip():
                notes = None

            sql = "insert into word (word, notes, pos_id) values (%s, %s, %s)"
            cursor.execute(sql, (word, notes, pos_id))
            cursor.execute("select last_insert_id() word_id")
            result = cursor.fetchone()
            word_id = result['word_id']

            save_attributes(word_id, attributes_adding, None, cursor)
            cursor.execute('commit')

            return get_word_by_id(word_id), 201  # this is already validated and jsonified

        except Exception as e:
            cursor.execute('rollback')
            return "error, transaction rolled back:  %s" % (str(e)), 500


@bp.route('/<int:relation_id>', methods=['PUT'])
def update_relation(relation_id):
    # any words in the payload are added to the relation.
    return "unimplemented", 501


@bp.route('/<int:relation_id>/batch_delete', methods=['PUT'])
def delete_from_relation(relation_id):
    return "unimplemented", 501


@bp.route('/<int:relation_id>', methods=['DELETE'])
def delete_relation(relation_id):
    return "unimplemented", 501


@bp.route('/wordlist/<int:wordlist_id>', methods=['POST'])
def create_relation_from_wordlist(wordlist_id):
    # no json payload needed here
    # make sure the wordlist exists, otherwise 400
    return "unimplemented", 501
