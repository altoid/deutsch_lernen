import mysql.connector.errors
from flask import Blueprint, request, abort, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import quiz_sql, dlernen_json_schema
import requests
import json
from contextlib import closing
import jsonschema
import sys
import os

# this is all of the code that implements the api.  all the routing functions for the
# /api urls are here.

bp = Blueprint('api', __name__)


@bp.route('/healthcheck')
def dbcheck():
    try:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            return 'OK', 200
    except Exception as e:
        return str(e), 500


