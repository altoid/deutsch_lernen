import mysql.connector.errors
from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema as js
from contextlib import closing
import jsonschema
import requests

# view functions for tags and word/tag linkages in wordlists

bp = Blueprint('api_wordlist_tag', __name__)

