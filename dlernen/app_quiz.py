from flask import Blueprint, url_for
from pprint import pprint, pformat
import requests
import click

bp = Blueprint('app_quiz', __name__)

QUIZ_KEY = 'definitions'


@bp.cli.command('quiz')
@click.argument('quiz_key')
@click.option('--wordlist_ids', '-l', multiple=True)
@click.option('--queries', '-q', multiple=True)
@click.option('--tags', '-t', multiple=True)
def quiz(quiz_key, wordlist_ids, queries, tags):
    print("quiz_key = |%s|, wordlist_ids = |%s|, queries = |%s|, tags = |%s|" % (
        quiz_key,
        pformat(wordlist_ids),
        pformat(queries),
        pformat(tags)
    ))
    # to run this, use the command:
    #   python -m flask --app run app_quiz quiz <quiz_key> [-l id -l id -l id ...]
    #
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    tags = list(set(tags))
    if tags and wordlist_ids:
        if len(wordlist_ids) > 1:
            print("only one list permitted if filtering by tags")
            return "OK", 200

    counter = 0
    if len(wordlist_ids) > 1:
        url = url_for('api_quiz.get_word_to_test',
                      wordlist_id=wordlist_ids,
                      quiz_key=quiz_key,
                      query=queries,
                      _external=True)
    else:
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      wordlist_id=wordlist_ids[0],
                      tag=tags,
                      quiz_key=quiz_key,
                      query=queries,
                      _external=True)

    while True:
        r = requests.get(url)
        if not r:
            message = "%s [%s]" % (r.text, r.status_code)
            print(message)
            return r.text, r.status_code

        attrs_to_test = r.json()

        if not attrs_to_test:
            print("es gibt keine Welten mehr zu erobern")
            break

        pprint(attrs_to_test)
        for attr in attrs_to_test:
            counter += 1
            if 'article' in attr:
                word = "%s %s" % (attr['article'], attr['word'])
            else:
                word = "%s" % (attr['word'])

            print("############ %s ###########" % word)
            prompt = "[%s] ===== %s ====> " % (counter, attr['attrkey'])

            answer = input(prompt).strip().casefold()
            while not answer:
                answer = input(prompt).strip().casefold()

            if answer == 'q':
                break

            correct = answer == attr['attrvalue'].casefold()

            if correct:
                print("=======> richtig")
            else:
                print("######## falsch: %s" % attr['attrvalue'])

            payload = {
                "quiz_id": attr['quiz_id'],
                "word_id": attr['word_id'],
                "attribute_id": attr['attribute_id'],
                "correct": correct,
            }

            r = requests.post(url_for('api_quiz.post_quiz_answer',
                                      quiz_key=quiz_key,
                                      _external=True), json=payload)

            if not r:
                message = "could not post quiz answer:  %s [%s]" % (r.text, r.status_code)
                return message, r.status_code

    print('bis bald')
