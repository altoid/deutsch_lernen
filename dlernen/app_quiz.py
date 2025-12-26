from flask import Blueprint, url_for
from pprint import pprint
import requests
import click
import random
from nltk.metrics.distance import edit_distance

bp = Blueprint('app_quiz', __name__)

QUIZ_KEY = 'definitions'


@bp.cli.command('quiz_words')
@click.option('--wordlist_ids', '-l', multiple=True)
@click.option('--queries', '-q', multiple=True)
def quiz_words(wordlist_ids, queries):
    # pick a definition and select the right german word for it.  as decoys, use words within a short levenshtein
    # distance away from the real answer.

    # get all the words
    url = url_for('api_word.get_words_in_wordlists', _external=True)
    r = requests.get(url)
    if not r:
        return r.text, r.status_code

    dictionary = r.json()

    while True:
        quiz_url = url_for('api_quiz_v2.get_word_to_test',
                           wordlist_id=wordlist_ids,
                           quiz_key=QUIZ_KEY,
                           query=queries,
                           _external=True)
        r = requests.get(quiz_url)
        if not r:
            return r.text, r.status_code

        attr_to_test = r.json()

        if not attr_to_test:
            print("es gibt keine Welten mehr zu erobern")

        # edit_distance is case sensitive
        distances = [(edit_distance(w['word'], attr_to_test['word'], transpositions=True), w['word']) for w in dictionary]

        distances = sorted(distances, key=lambda x: (x[0], x[1]))
        candidates = [x[1] for x in distances[1:4]]  # distances[0] will be the word itself
        candidates.append(attr_to_test['word'])
        random.shuffle(candidates)

        print()
        print("################## %s" % attr_to_test['attrvalue'])
        print()

        for i in range(len(candidates)):
            print("%s: %s" % (i, candidates[i]))

        # keep pestering for usable response
        while True:
            prompt = "answer, q to quit  --> "
            answer = input(prompt).strip().lower()
            if not answer:
                continue

            if answer[0] == 'q':
                return "OK", 200

            try:
                answer = int(answer)
                if 0 <= answer < len(candidates):
                    break
            except ValueError:
                pass

        if candidates[answer] == attr_to_test['word']:
            attr_to_test['correct'] = True
            print("richtig")
        else:
            attr_to_test['correct'] = False
            print("falsch")

        r = requests.post(url_for('api_quiz_v2.post_quiz_answer',
                                  quiz_key=QUIZ_KEY,
                                  _external=True), json=attr_to_test)

        if not r:
            print(r.text, r.status_code)
            return r.text, r.status_code


@bp.cli.command('quiz_definitions')
@click.option('--wordlist_ids', '-l', multiple=True)
@click.option('--queries', '-q', multiple=True)
@click.option('--tags', '-t', multiple=True)
def quiz_definitions(wordlist_ids, queries, tags):
    # to run this, use the command:
    #   python -m flask --app run app_quiz_definitions quiz_definitions [-l id -l id -l id ...]
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
        url = url_for('api_quiz_v2.get_word_to_test',
                      wordlist_id=wordlist_ids,
                      quiz_key=QUIZ_KEY,
                      query=queries,
                      _external=True)
    else:
        url = url_for('api_quiz_v2.get_word_to_test_single_wordlist',
                      wordlist_id=wordlist_ids[0],
                      tag=tags,
                      quiz_key=QUIZ_KEY,
                      query=queries,
                      _external=True)

    while True:
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
            "attribute_id": attr_to_test['attribute_id']
        }

        while len(answer) == 0:
            answer = input(prompt).strip().lower()

        payload['correct'] = answer.startswith('y')

        r = requests.post(url_for('api_quiz_v2.post_quiz_answer',
                                  quiz_key=QUIZ_KEY,
                                  _external=True), json=payload)

        if not r:
            return r.text, r.status_code

    print('bis bald')
