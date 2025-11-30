from flask import Blueprint, url_for
from pprint import pprint
import requests
import click

bp = Blueprint('app_quiz', __name__)


@bp.cli.command('quiz_definitions')
@click.option('--wordlist_ids', '-l', multiple=True)
@click.option('--queries', '-q', multiple=True)
def quiz_definitions(wordlist_ids, queries):
    # to run this, use the command:
    #   python -m flask --app run app_quiz_definitions quiz_definitions [-l id -l id -l id ...]
    #
    # it has to be invoked from the dlernen directory.
    # need -l for each list id because click sucks but we can't use argparse.

    counter = 0
    while True:
        url = url_for('api_quiz_v2.get_word_to_test',
                      wordlist_id=wordlist_ids,
                      quiz_key='definitions',
                      query=queries,
                      _external=True)
        r = requests.get(url)
        if not r:
            return r.text, r.status_code

        attr_to_test = r.json()

        if not attr_to_test:
            print("es gibt keine Welten mehr zu erobern")
            break

        counter += 1
        print("[%s]" % counter, end=' ')

        if 'article' in attr_to_test:
            print(attr_to_test['article'], end=' ')

        print(attr_to_test['word'])
        prompt = "hit return for answer, q to quit:  --> "
        answer = input(prompt).strip().lower()

        if answer.startswith('q'):
            break

        print(attr_to_test['attrvalue'])

        prompt = "correct? --> "
        answer = input(prompt).strip().lower()

        payload = {
            "quiz_id": attr_to_test['quiz_id'],
            "word_id": attr_to_test['word_id'],
            "attribute_id": attr_to_test['attribute_id'],
            "presentation_count": attr_to_test['presentation_count'],
            "correct_count": attr_to_test['correct_count']
        }

        while len(answer) == 0:
            answer = input(prompt).strip().lower()

        if answer.startswith('y'):
            payload['correct_count'] += 1

        payload['presentation_count'] += 1

        r = requests.post(url_for('api_quiz.post_quiz_answer', _external=True), data=payload)

    print('bis bald')
