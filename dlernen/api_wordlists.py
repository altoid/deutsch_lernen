from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema

import requests
import json
from contextlib import closing
import jsonschema

# view functions for /api/wordlists URLs are here.

bp = Blueprint('api_wordlists', __name__, url_prefix='/api/wordlists')


@bp.route('/batch_delete', methods=['PUT'])
def delete_wordlists():
    try:
        payload = request.get_json()  # comes in as an array of ints, not a dict.
        jsonschema.validate(payload, dlernen_json_schema.WORDLISTS_DELETE_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    if len(payload):
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = "delete from wordlist where id = %s"
            args = [[int(x)] for x in payload]
            cursor.executemany(sql, args)
            dbh.commit()

    return 'OK'


@bp.route('', methods=['GET'])
def get_wordlists():
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        wordlist_ids = request.args.getlist('wordlist_id')
        if wordlist_ids:
            wordlist_ids = list(set(wordlist_ids))
            where_clause = "where wordlist.id in (%s)" % (','.join(['%s'] * len(wordlist_ids)))
        else:
            where_clause = ''

        sql = """
with wordlist_counts as
(
    select wordlist_id, sum(c) lcount from
    (
        select wordlist_id, count(*) c
        from wordlist_word
        group by wordlist_id
    ) a
    group by wordlist_id
)
select name, id wordlist_id, ifnull(lcount, 0) count, sqlcode
from wordlist
left join wordlist_counts wc on wc.wordlist_id = wordlist.id
%(where_clause)s
order by name
        """ % {
            'where_clause': where_clause
        }

        cursor.execute(sql, wordlist_ids)
        rows = cursor.fetchall()

        # maps list id to list info
        dict_result = {}

        for r in rows:
            # the connector is returning the count as a Decimal, have to convert it to int

            list_type = 'empty'
            if bool(r['sqlcode']):
                list_type = 'smart'
            elif r['count'] > 0:
                list_type = 'standard'

            dict_result[r['wordlist_id']] = {
                'name': r['name'],
                'wordlist_id': r['wordlist_id'],
                'list_type': list_type,
                'count': int(r['count'])
            }

            if r['sqlcode']:
                cursor.execute(r['sqlcode'])
                smartlist_rows = cursor.fetchall()
                dict_result[r['wordlist_id']]['count'] = len(smartlist_rows)

        result = list(dict_result.values())
        jsonschema.validate(result, dlernen_json_schema.WORDLISTS_RESPONSE_SCHEMA)
        return result


@bp.route('/<int:word_id>')
def get_wordlists_by_word_id(word_id):
    word_id = int(word_id)
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # find standard lists that this word is in
        sql = """
        select
        wl.id wordlist_id
        from wordlist wl
        inner join wordlist_word ww
        on ww.wordlist_id = wl.id
        where word_id = %s
        order by wl.name
        """
        cursor.execute(sql, (word_id,))
        rows = cursor.fetchall()
        standard_lists = [r['wordlist_id'] for r in rows]

        # find smart lists that this word is in!
        # get all the sql
        sql = """
        select name, sqlcode, id wordlist_id
        from wordlist
        where sqlcode is not null
        """

        smart_lists = []
        cursor.execute(sql)
        code_results = cursor.fetchall()
        for r in code_results:
            sqlcode = r['sqlcode']
            if not sqlcode:
                continue

            cursor.execute(r['sqlcode'])
            results_for_list = cursor.fetchall()
            results_for_list = [x['word_id'] for x in results_for_list]
            if word_id in results_for_list:
                smart_lists.append(r['wordlist_id'])

        wordlist_ids = standard_lists + smart_lists

        result = []
        if wordlist_ids:
            url = url_for('api_wordlists.get_wordlists', wordlist_id=wordlist_ids, _external=True)
            r = requests.get(url)
            if not r:
                return r.text, r.status_code

            result = json.loads(r.text)
            result = sorted(result, key=lambda x: x['name'].casefold())

            # validation happens in get_wordlists so we don't need to do it here.

        return result


