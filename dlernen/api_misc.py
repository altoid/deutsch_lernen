from flask import Blueprint, current_app, url_for
from mysql.connector import connect
from dlernen import dlernen_json_schema
from pprint import pprint
from contextlib import closing
import jsonschema
import click
import requests

# miscellaneous /api endpoints are here.

bp = Blueprint('api_misc', __name__)


@bp.route('/healthcheck')
def dbcheck():
    try:
        with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            return 'OK', 200
    except Exception as e:
        return str(e), 500


@bp.route('/api/gender_rules')
def gender_rules():
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        query = """
        select article, rule
        from gender_rule
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


@bp.route('/api/pos')
def get_pos():
    """
    fetch the part-of-speech info from the database and format it
    """
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select p.name, a.attrkey, a.id AS attribute_id, pf.sort_order
        from pos_form pf
        inner join pos p on p.id = pf.pos_id
        inner join attribute a on a.id = pf.attribute_id;
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        temp_result = {}
        for r in rows:
            if r['name'] not in temp_result:
                temp_result[r['name']] = []
            temp_result[r['name']].append(
                {
                    "attrkey": r['attrkey'],
                    "attribute_id": r['attribute_id'],
                    "sort_order": r['sort_order']
                }
            )

        result = []
        for k in temp_result.keys():
            result.append(
                {
                    "pos_name": k.lower(),
                    "attributes": temp_result[k]
                }
            )

        jsonschema.validate(result, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

        return result


@bp.route('/api/config')
def get_config():
    d = dict(current_app.config)

    # timedelta objects aren't serializable, so do this
    d['PERMANENT_SESSION_LIFETIME'] = d['PERMANENT_SESSION_LIFETIME'].total_seconds()

    return d, 200


@bp.cli.command('patch_words')
@click.option('--wordlist_ids', '-l', multiple=True)
def patch_words(wordlist_ids):
    # to run this, use the command:  python -m flask --app run api_misc patch_words
    wordlist_ids = list(wordlist_ids)

    args = None
    if wordlist_ids:
        args = ','.join(wordlist_ids)

    url = url_for('api_word.get_words_in_wordlists', wordlist_id=args, _external=True)

    r = requests.get(url)
    if not r:
        return 'oh shit', r.status_code

    result = r.json()

    words_to_patch = []

    # get all the verbs
    attrs_to_patch = {
        'third_person_past',
        #        'past_participle'
    }
    result = list(filter(lambda x: x['pos_name'] == 'Verb', result))
    for w in result:
        tpp = list(filter(lambda x: x['attrkey'] in attrs_to_patch and x['attrvalue'] is None, w['attributes']))
        if tpp:
            words_to_patch.append(w)

    print("found %s verbs to patch" % (len(words_to_patch)))

    if not words_to_patch:
        print("nothing to do")
        return 'OK', 200

    # from the first word, extract all of the attr keys and their sort orders.  these are the same for
    # each of the words retrieved.
    # TODO this will have to do until i make an api call that retrieves the attr keys and sort orders for all
    #   the parts of speech.
    sort_order_to_attrkey = {}
    for a in words_to_patch[0]['attributes']:
        if a['attrkey'] in attrs_to_patch:
            sort_order_to_attrkey[a['sort_order']] = a['attrkey']

#    pprint(sort_order_to_attrkey)
    ordering = sorted(list(sort_order_to_attrkey.keys()))
#    pprint(ordering)

    payload = {
        "attributes_adding": []
    }

    for p in words_to_patch:
        attrkey_to_attrvalue = {}
        for a in p['attributes']:
            if a['attrkey'] in attrs_to_patch:
                attrkey_to_attrvalue[a['attrkey']] = a['attrvalue']
#        pprint(attrkey_to_attrvalue)

        payload['attributes_adding'].clear()

        for i in ordering:
            k = sort_order_to_attrkey[i]
            v = attrkey_to_attrvalue[k]

            if v:
                # don't bash an already-set value
                continue

            answer = input("%s [%s] ---> " % (p['word'], k))
            answer = answer.strip()

            if not answer:
                # skip to the next one
                continue

            if answer == 'q':
                return 'OK', 200

            d = {
                "attrvalue": answer,
                "attrkey": sort_order_to_attrkey[i]
            }
            payload["attributes_adding"].append(d)

#        pprint(payload)

        url = url_for("api_word.update_word", word_id=p['word_id'], _external=True)
        r = requests.put(url, json=payload)
        if r.status_code != 200:
            pprint(p)
            return 'BAD', r.status_code

