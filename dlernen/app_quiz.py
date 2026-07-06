from flask import Blueprint, url_for
from pprint import pprint, pformat
import requests
import click
from dlernen import api_quiz
from dlernen.dlernen_json_schema import ATTRIBUTES
bp = Blueprint('app_quiz', __name__)

QUIZ_KEY = 'definitions'


@bp.cli.command('quiz')
@click.argument('quiz_key')
@click.option('--wordlist_id', '-l')
@click.option('--selector', '-s')
@click.option('--tags', '-t', multiple=True)
def quiz(quiz_key, wordlist_id, selector, tags):
    print("quiz_key = |%s|, wordlist_id = |%s|, selector = |%s|, tags = |%s|" % (
        quiz_key,
        pformat(wordlist_id),
        pformat(selector),
        pformat(tags)
    ))

    if not wordlist_id:
        print("wordlist id is required for now")
        return "OK", 200

    if selector and selector not in api_quiz.Selector:
        print("invalid selector:  %s" % selector)
        return "OK", 200
    
    # to run this, use the command:
    #   python -m flask --app run app_quiz quiz <quiz_key> [-l id -l id -l id ...]
    #
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    tags = list(set(tags))

    counter = 0
    url = url_for('api_quiz.get_words_in_wordlist',
                  quiz_key=quiz_key,
                  wordlist_id=wordlist_id,
                  tag=tags,
                  selector=selector,
                  _external=True)

    r = requests.get(url)
    if not r:
        message = "%s [%s]" % (r.text, r.status_code)
        print(message)
        return r.text, r.status_code

    words_to_test = r.json()
    if not words_to_test:
        print("es gibt keine Welten mehr zu erobern")
        return "OK", 200

    print("testing %s words" % len(words_to_test))

    stop_i_want_to_get_off = False

    for candidate in words_to_test:
        if stop_i_want_to_get_off:
            break

        counter += 1

        word = candidate['word']
        if 'article' in candidate:
            word = "%s %s" % (candidate['article'], word)

        print("############ %s ###########" % word)
        for attr in candidate[ATTRIBUTES]:
            prompt = "[%s] ===== %s ====> " % (counter, attr['attrkey'])

            answer = input(prompt).strip().casefold()
            while not answer:
                answer = input(prompt).strip().casefold()

            if answer == 'q':
                stop_i_want_to_get_off = True
                break

            correct = answer == attr['attrvalue'].casefold()

            if correct:
                print("=======> richtig")
            else:
                print("######## falsch: %s" % attr['attrvalue'])

            payload = {
                "word_id": candidate['word_id'],
                "attrkey": attr['attrkey'],
                "correct": correct,
            }

            r = requests.post(url_for('api_quiz.post_quiz_score',
                                      quiz_key=quiz_key,
                                      _external=True), json=payload)

            if not r:
                message = "could not post quiz answer:  %s [%s]" % (r.text, r.status_code)
                return message, r.status_code

    print('bis bald')
