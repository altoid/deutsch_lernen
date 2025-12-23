from flask import Blueprint, url_for
from pprint import pprint
import requests
import click
import random

bp = Blueprint('app_urmverb', __name__)


def is_irregular_verb(word):
    # returns:
    #
    # True  - yes, this is an irregular verb
    # False - not an irregular verb
    # None  - not in the dictionary, not a verb, or we can't tell (e.g. second_person_singular not defined)

    url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
    r = requests.get(url)
    if not r:
        raise Exception("%s [%s]", (r.text, r.status_code))

    pos_structure = r.json()

    verb_part = list(filter(lambda x: x['pos_name'] == 'verb', pos_structure))[0]

    word_id = verb_part['word_id']
    if not word_id:
        return None

    sps = list(filter(lambda x: x['attrkey'] == 'second_person_singular', verb_part['attributes']))[0]['attrvalue']
    if not sps:
        return None

    tps = list(filter(lambda x: x['attrkey'] == 'third_person_singular', verb_part['attributes']))[0]['attrvalue']
    if not tps:
        return None

    # if there is a separable prefix, toss it.
    sps_parts = sps.split()
    if len(sps_parts) > 1:
        prefix = sps_parts[1]
        stem = word[len(prefix):]
    else:
        stem = word

    # get the verb stem
    if not stem.endswith('n'):
        raise Exception("what the hell kind of verb doesn't end with n: [%s]" % word)

    stem = stem[:-1]
    if stem.endswith('e'):
        stem = stem[:-1]

    # compare verb stem with sps
    l = min(len(stem), len(sps_parts[0]))
    if stem[:l] != sps_parts[0][:l]:
        return True

    tps_parts = tps.split()
    l = min(len(stem), len(tps_parts[0]))
    if stem[:l] != tps_parts[0][:l]:
        return True

    return False


@bp.cli.command('test_irr_verb')
def test_irr_verb():
    word = 'sehen'
    print(word, is_irregular_verb(word))

