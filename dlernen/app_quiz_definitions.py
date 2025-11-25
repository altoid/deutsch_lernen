from flask import Blueprint, url_for
from pprint import pprint
import click
import requests
from app_common import get_next_word_to_test
import click

bp = Blueprint('app_quiz_definitions', __name__)


@bp.cli.command('quiz_definitions')
@click.option('--wordlist_ids', '-l', multiple=True)
def quiz_definitions(wordlist_ids):
    # to run this, use the command:
    #   python -m flask --app run app_quiz_definitions quiz_definitions [-l id -l id -l id ...]
    #
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    counter = 0
    while True:
        row = get_next_word_to_test(wordlist_ids, 'definitions')

        if not row:
            print("es gibt keine Welten mehr zu erobern")
            break

        counter += 1
        print("[%s]" % counter, end=' ')

        if 'article' in row:
            print(row['article'], end=' ')

        print(row['word'])
        prompt = "hit return for answer, q to quit:  --> "
        answer = input(prompt).strip().lower()

        if answer.startswith('q'):
            break

        print(row['attributes']['definition']['attrvalue'])

        prompt = "correct? --> "
        answer = input(prompt).strip().lower()

        payload = {
            "quiz_id": row['quiz_id'],
            "word_id": row['word_id'],
            "attribute_id": row['attributes']['definition']['attribute_id'],
            "presentation_count": row['attributes']['definition']['presentation_count'],
            "correct_count": row['attributes']['definition']['correct_count']
        }

        while len(answer) == 0:
            answer = input(prompt).strip().lower()

        if answer.startswith('y'):
            payload['correct_count'] += 1

        payload['presentation_count'] += 1

        r = requests.post(url_for('api_quiz.post_quiz_answer', _external=True), data=payload)

    print('bis bald')
