from flask import Blueprint, request, url_for, current_app
from pprint import pprint
from mysql.connector import connect
import mysql.connector.errors
from dlernen.dlernen_json_schema import \
    WORDLISTS_DELETE_PAYLOAD_SCHEMA, \
    WORDLISTS_RESPONSE_SCHEMA
from dlernen.decorators import js_validate_result, js_validate_payload
from contextlib import closing

# view functions for /api/wordlists URLs are here.

bp = Blueprint('api_wordlists', __name__, url_prefix='/api/wordlists')


@bp.route('/batch_delete', methods=['PUT'])
@js_validate_payload(WORDLISTS_DELETE_PAYLOAD_SCHEMA)
def delete_wordlists():
    payload = request.get_json()

    if len(payload):
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = "delete from wordlist where id = %s"
            args = [[int(x)] for x in payload]
            cursor.executemany(sql, args)
            dbh.commit()

    return 'OK'


@js_validate_result(WORDLISTS_RESPONSE_SCHEMA)
def __get_wordlists(wordlist_ids, cursor):
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
            try:
                cursor.execute(r['sqlcode'])
                smartlist_rows = cursor.fetchall()
                dict_result[r['wordlist_id']]['count'] = len(smartlist_rows)
            except mysql.connector.errors.ProgrammingError as f:
                # this will happen if the sqlcode is invalid.
                # set the count to -1 and let the client deal with it.
                dict_result[r['wordlist_id']]['count'] = -1

    return list(dict_result.values())


@bp.route('', methods=['GET'])
def get_wordlists():
    wordlist_ids = request.args.getlist('wordlist_id')
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            return __get_wordlists(wordlist_ids, cursor)

        except Exception as e:
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/<int:word_id>')
def get_wordlists_by_word_id(word_id):
    word_id = int(word_id)
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
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

            return __get_wordlists(wordlist_ids, cursor)

        except Exception as e:
            cursor.execute('rollback')
            return str(e), 500


