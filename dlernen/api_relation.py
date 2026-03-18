from flask import Blueprint, request, current_app, url_for
import requests
from pprint import pprint, pformat
from mysql.connector import connect
from dlernen import common
from dlernen.dlernen_json_schema import get_validator, \
    RELATION_RESPONSE_SCHEMA, \
    RELATION_ARRAY_RESPONSE_SCHEMA, \
    RELATION_PAYLOAD_SCHEMA
from contextlib import closing
import jsonschema

bp = Blueprint('api_relation', __name__, url_prefix='/api/relation')


@bp.route('/<int:relation_id>')
def get_relation(relation_id):
    return "unimplemented", 501


@bp.route('', methods=['POST'])
def create_relation():
    return "unimplemented", 501


@bp.route('/<int:relation_id>', methods=['PUT'])
def update_relation(relation_id):
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
    return "unimplemented", 501
