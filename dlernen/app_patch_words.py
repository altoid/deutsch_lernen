from flask import Blueprint, url_for
from pprint import pprint
import click
import requests

bp = Blueprint('app_patch_words', __name__)


@bp.cli.command('patch_words')
@click.option('--wordlist_ids', '-l', multiple=True)
@click.option('--attributes', '-a', multiple=True)
def patch_words(wordlist_ids, attributes):
    # to run this, use the command:  python -m flask --app run app_patch_words patch_words [-l id -l id -l id ...]
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    url = url_for('api_pos.get_pos', _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    pos_structure = r.json()
    verb_structure = list(filter(lambda x: x['pos_name'].casefold() == 'verb', pos_structure))[0]

    verb_attrs = {x['attrkey'] for x in verb_structure['attributes']}
    sort_order_to_attrid = {x['sort_order']: x['attribute_id'] for x in verb_structure['attributes']}
    wordlist_ids = list(wordlist_ids)

    attrkeys_to_patch = set(attributes) if attributes else verb_attrs

    unknown_attrs = attrkeys_to_patch - verb_attrs
    if unknown_attrs:
        message = "unknown attributes:  %s" % unknown_attrs
        print(message)
        return message, 400

    url = url_for('api_word.get_words_in_wordlists', wordlist_id=wordlist_ids, _external=True)

    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    result = r.json()

    words_to_patch = []

    result = list(filter(lambda x: x['pos_name'] == 'Verb', result))
    for w in result:
        tpp = list(filter(lambda x: x['attrkey'] in attrkeys_to_patch and x['attrvalue'] is None, w['attributes']))
        if tpp:
            words_to_patch.append(w)

    print("found %s verbs to patch" % (len(words_to_patch)))

    if not words_to_patch:
        print("nothing to do")
        return 'OK', 200

    payload = {
        "attributes": []
    }

    for p in words_to_patch:
        attrs_to_patch = list(filter(lambda x: x['attrkey'] in attrkeys_to_patch and x['attrvalue'] is None,
                                     p['attributes']))

        keys_to_values = {x['attrkey']: x['attrvalue'] for x in attrs_to_patch}
        sort_order_to_attrkey = {x['sort_order']: x['attrkey'] for x in attrs_to_patch}
        ordering = sorted(list(sort_order_to_attrkey.keys()))

        payload['attributes'].clear()

        print("============================= %s" % p['word'])
        for i in ordering:
            k = sort_order_to_attrkey[i]
            v = keys_to_values[k]

            if v:
                # don't bash an already-set value
                continue

            answer = input("[%s] ---> " % (k))
            answer = answer.strip()

            if not answer:
                # skip to the next one
                continue

            if answer == 'q':
                return 'OK', 200

            d = {
                "attrvalue": answer,
                "attribute_id": sort_order_to_attrid[i]
            }
            payload["attributes"].append(d)

        url = url_for("api_word.update_word", word_id=p['word_id'], _external=True)
        r = requests.put(url, json=payload)
        if not r:
            pprint(p)
            print(r.text)
            return 'BAD', r.status_code

