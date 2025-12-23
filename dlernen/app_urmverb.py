from flask import Blueprint, url_for
from pprint import pprint
import requests
import click

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

    second_person_singular = list(filter(lambda x: x['attrkey'] == 'second_person_singular',
                                         verb_part['attributes']))[0]['attrvalue']
    if not second_person_singular:
        return None

    third_person_singular = list(filter(lambda x: x['attrkey'] == 'third_person_singular',
                                        verb_part['attributes']))[0]['attrvalue']
    if not third_person_singular:
        return None

    third_person_past = list(filter(lambda x: x['attrkey'] == 'third_person_past',
                                    verb_part['attributes']))[0]['attrvalue']
    if not third_person_past:
        return None

    # if there is a separable prefix, toss it.
    second_person_singular_parts = second_person_singular.split()
    if len(second_person_singular_parts) > 1:
        prefix = second_person_singular_parts[1]
        stem = word[len(prefix):]
    else:
        stem = word

    # a very few verbs are irregular not because of stem vowel changes, but because
    # the third-person-singular does not end with a 't'.  they are:  the modal auxiliaries, werden, and wissen.
    # these all have stem vowel changes too.  EXCEPT for sollen.  this is the only verb where there is no
    # stem vowel change but also no 't' in the third person singular.  so, hard code it.

    if word == 'sollen':
        return True

    # get the verb stem
    if not stem.endswith('n'):
        raise Exception("what the hell kind of verb doesn't end with n: [%s]" % word)

    # if the verb ends with -en, get rid of this last 'e' too
    stem = stem[:-1]
    if stem.endswith('e'):
        stem = stem[:-1]

    # compare verb stem with second_person_singular
    l = min(len(stem), len(second_person_singular_parts[0]))
    if stem[:l] != second_person_singular_parts[0][:l]:
        return True

    third_person_singular_parts = third_person_singular.split()
    l = min(len(stem), len(third_person_singular_parts[0]))
    if stem[:l] != third_person_singular_parts[0][:l]:
        return True

    third_person_past_parts = third_person_past.split()
    l = min(len(stem), len(third_person_past_parts[0]))
    if stem[:l] != third_person_past_parts[0][:l]:
        return True

    return False


@bp.cli.command('update_irregular_verb_wordlist')
def update_irregular_verb_wordlist():
    # get all the verbs and spit out the ones that are irregular

    url = url_for('api_word.get_words_in_wordlists', wordlist_id=[], _external=True)

    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    result = r.json()

    irregular_verbs = []
    all_verbs = list(filter(lambda x: x['pos_name'].casefold() == 'verb', result))
    all_verb_word_ids = [x['word_id'] for x in all_verbs]
    for w in all_verbs:
        if is_irregular_verb(w['word']):
            irregular_verbs.append(w['word_id'])

    # delete all the known words from the wordlist first.  this is overkill, since we are deleting the ids for
    # every verb.
    payload = {
        "word_ids": all_verb_word_ids
    }

    # stuff them all into the irregular verbs wordlist (id 32)
    wordlist_id = 32
    url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.post(url, json=payload)
    if not r:
        message = "could not flush word list:  %s" % r.text
        print(message)
        return message, r.status_code

    r = requests.put(url_for('api_wordlist.add_words_by_id', wordlist_id=wordlist_id, _external=True),
                     json=irregular_verbs)
    if not r:
        print(r.text)
        return r.text, r.status_code

    # need to refresh, so that unknown words that are defined will disappear from the unknown list.

    r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True))
    if not r:
        print(r.text)
        return r.text, r.status_code
    wordlist = r.json()

    for unknown_word in wordlist['unknown_words']:
        r = requests.put(url_for('api_wordlist.refresh_wordlists', _external=True),
                         json={
                             "word": unknown_word
                         })
        if r.status_code == 404:
            # word is still unknown.  keep going.
            continue

        if not r:
            message = "could not refresh word:  %s (%s, %s)" % (unknown_word, r.text, r.status_code)
            print(message)
            return message, r.status_code

