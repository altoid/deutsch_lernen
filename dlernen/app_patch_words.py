from flask import Blueprint, url_for
from pprint import pprint, pformat
import click
import requests
import random

bp = Blueprint('app_patch_words', __name__)


@bp.cli.command('patch_words')
@click.option('--wordlist_id', '-l', multiple=True)
@click.option('--quiz_key', '-k')
def patch_words(wordlist_id, quiz_key):
    # to run this, use the command:  python -m flask --app run app_patch_words patch_words [-l id -l id -l id ...]
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    wordlist_ids = list(set(map(int, wordlist_id)))

    if quiz_key:
        r = requests.get(url_for('api_quiz.get_incomplete_words',
                                 quiz_key=quiz_key,
                                 wordlist_id=wordlist_ids,
                                 _external=True))
    else:
        r = requests.get(url_for('api_words.get_incomplete_words',
                                 wordlist_id=wordlist_ids,
                                 _external=True))

    if not r:
        print(r.text)
        return r.text, r.status_code

    words_to_patch = r.json()

    # scramble the presentation order of the words.  https://youtu.be/i6nEiXtwfT4
    random.shuffle(words_to_patch)

    print("found %s words to patch" % (len(words_to_patch)))
    if not words_to_patch:
        print("nothing to do")
        return 'OK', 200

    counter = 0
    remaining = len(words_to_patch)

    for w in words_to_patch:
        counter += 1
        remaining -= 1

        print("[%s/%s] ============================= %s (%s) [%s]" % (counter, remaining, w['word'], w['pos_name'],
                                                                      w['word_id']))
        for attr in w['attributes']:
            if attr['attrvalue']:
                continue

            answer = input("[%s] ---> " % attr['attrkey'])
            answer = answer.strip()

            if not answer:
                # skip to the next one
                continue

            if answer == 'q':
                print('bis bald')
                return 'OK', 200

            payload = {
                'attributes': [
                    {
                        "attrvalue": answer,
                        "attribute_id": attr['attribute_id']
                    }
                ]
            }

            url = url_for("api_word.update_word", word_id=w['word_id'], _external=True)
            r = requests.put(url, json=payload)
            if not r:
                pprint(w)
                print(r.text)
                return 'BAD', r.status_code
