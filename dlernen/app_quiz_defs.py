from flask import Blueprint, url_for
from pprint import pprint
import requests
import click
import random
import api_quiz

bp = Blueprint('app_quiz_defs', __name__)

QUIZ_KEY = 'definitions'
WORDLISTS = {}  # maps wordlist_ids to names
QUERIES = {'oldest_first'}
TAGS = set()
COUNTER = 0
WORDS_MISSED = {}  # maps word_ids to QUIZ_RESPONSE_SCHEMA objects


def unimplemented():
    print("""
    #############################
    #       unimplemented       #
    #############################
    """)


def quit_program():
    print('bis bald')


def main_menu():
    global WORDLISTS

    options_in_display_order = sorted(CALLBACKS.keys(), key=lambda x: CALLBACKS[x]['display_order'])
    if len(WORDLISTS) != 1:
        options_in_display_order.remove('tags')

    print("""
Hauptmenü:
""")

    for c in options_in_display_order:
        print("    %-10s --> %s" % (c, CALLBACKS[c]['tagline']))
    print()

    while True:
        prompt = '---> '
        answer = input(prompt).strip().lower()
        if not answer:
            continue

        if answer not in options_in_display_order:
            print("not an option:  %s" % answer)
            continue

        break

    return CALLBACKS[answer]['callback']


def reset():
    global WORDLISTS
    global QUERIES
    global TAGS
    global COUNTER
    global WORDS_MISSED

    WORDLISTS.clear()
    QUERIES = {'oldest_first'}
    TAGS.clear()
    COUNTER = 0
    WORDS_MISSED.clear()


def select_lists():
    global WORDLISTS
    global TAGS

    # changing the list selection will blow away saved state!
    reset()

    wordlist_ids = []

    menu = """
c - clear selection
s - show selection
m - show menu
r - return to main menu
or enter list of wordlist_ids, space separated
"""

    print(menu)
    while True:
        prompt = '[select lists] ---> '
        answer = input(prompt).strip().lower()
        if not answer:
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'c':
            WORDLISTS.clear()
            TAGS.clear()
            print("selection cleared")
            continue

        if answer == 's':
            if not WORDLISTS:
                print("no lists selected, defaults to whole dictionary")
            else:
                for k, v in WORDLISTS.items():
                    print("[%s] - %s" % (k, v))
            continue

        if answer == 'r':
            break

        try:
            wordlist_ids += list(map(int, answer.split()))
        except ValueError as e:
            print("bad dog")
            continue

        unknown_wordlist_ids = set()
        for id in wordlist_ids:
            r = requests.get(url_for('api_wordlist.get_wordlist_metadata',
                                     wordlist_id=id,
                                     _external=True))
            if r.status_code == 404:
                unknown_wordlist_ids.add(id)
                continue

            if not r:
                print(r.text, r.status_code)
                continue

            obj = r.json()

            WORDLISTS[id] = obj['name']

        print("list_ids:  ", end=' ')
        pprint(set(WORDLISTS.keys()))

        if unknown_wordlist_ids:
            print("unknown wordlist_ids:  ", end=' ')
            pprint(set(unknown_wordlist_ids))

        # TODO - don't forget about the tags


def status():
    global WORDLISTS
    global TAGS
    global COUNTER
    global WORDS_MISSED
    global QUERIES

    print("""
****************************************
*
*         Status
*
****************************************

""")

    print("""
Lists:""")
    if WORDLISTS:
        for k, v in WORDLISTS.items():
            print("[%s] - %s" % (k, v))
    else:
        print("** entire dictionary")

    print("""
Tags:""")
    if TAGS:
        print("current tags:  ", end= ' ')
        pprint(TAGS)
    else:
        print("** no tags")

    print("""
Queries:""")
    for q in QUERIES:
        print(q)

    print("""
Words tested this session:  %s""" % COUNTER)

    print("""
Words missed this session:  %s""" % len(WORDS_MISSED))


def select_tags():
    global TAGS

    menu = """
c - clear selection
s - show selection
m - show menu
r - return to main menu
or enter list of tags, space separated
"""

    print(menu)

    # FIXME - let's hope none of the menu options are tags

    while True:
        prompt = '[enter tags] ---> '
        answer = input(prompt).strip().casefold()
        if not answer:
            continue

        if answer == 'c':
            TAGS.clear()
            continue

        if answer == 's':
            print("current tags:  ", end=' ')
            pprint(TAGS)
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            break

        tags = set(answer.split())
        TAGS |= tags
        print("current tags:  ", end=' ')
        pprint(TAGS)


def select_queries():
    global QUERIES

    menu = """
c - clear selection
s - show selection
q - show possible queries
m - show menu
r - return to main menu
or enter list of query names, space separated
"""

    print(menu)
    print("current queries:  ", end=' ')
    pprint(QUERIES)
    possible_queries = set(api_quiz.DEFINED_QUERIES.keys())

    while True:
        prompt = '[select queries] ---> '
        answer = input(prompt).strip().casefold()
        if not answer:
            continue

        if answer == 'c':
            QUERIES.clear()
            print("selection cleared")
            continue

        if answer == 's':
            print("selection:  ", end=' ')
            pprint(QUERIES)
            continue

        if answer == 'q':
            print("possible queries:  ", end=' ')
            pprint(set(api_quiz.DEFINED_QUERIES.keys()))
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            break

        given = set(answer.split())
        unknown = given - possible_queries
        QUERIES |= given & possible_queries

        print("selection:  ", end=' ')
        pprint(QUERIES)
        if unknown:
            print("unknown queries:  ", end=' ')
            pprint(unknown)


def test_word(attr_to_test):
    # attr_to_test is a QUIZ_RESPONSE_SCHEMA object, with an 'article' if the word is a noun.

    global COUNTER

    if 'article' in attr_to_test:
        print("[%s] %s %s" % (COUNTER, attr_to_test['article'], attr_to_test['word']))
    else:
        print("[%s] %s" % (COUNTER, attr_to_test['word']))

    prompt = "hit return for answer, r for main menu, h for hint:  --> "
    answer = input(prompt).strip().lower()

    if answer.startswith('h'):
        # show wordlists this word is in.
        r = requests.get(url_for('api_wordlist.get_wordlists_by_word_id',
                                 word_id=attr_to_test['word_id'],
                                 _external=True))
        if not r:
            message = "could not get wordlists for word id %s:  [%s, %s]" % (attr_to_test['word_id'], r.text,
                                                                             r.status_code)
            print(message)
            return

        obj = r.json()
        for n in obj:
            r = requests.get(url_for('api_wordlist_tag.get_tags',
                                     wordlist_id=n['wordlist_id'],
                                     word_id=attr_to_test['word_id'],
                                     _external=True))
            if not r:
                message = "could not get tags for word id %s:  [%s, %s]" % (
                    attr_to_test['word_id'], r.text,
                    r.status_code)
                print(message)
                return

            tags_response = r.json()
            tags = ', '.join(tags_response['tags'])
            if tags:
                print("%s [%s:  %s]" % (n['name'], n['wordlist_id'], tags))
            else:
                print("%s [%s]" % (n['name'], n['wordlist_id']))

    if answer.startswith('r'):
        return

    print(attr_to_test['attrvalue'])

    prompt = "correct? --> "
    answer = input(prompt).strip().lower()
    while not answer:
        answer = input(prompt).strip().lower()

    payload = {
        "quiz_id": attr_to_test['quiz_id'],
        "word_id": attr_to_test['word_id'],
        "attribute_id": attr_to_test['attribute_id'],
        "correct": answer.startswith('y')
    }

    r = requests.post(url_for('api_quiz.post_quiz_answer',
                              quiz_key=QUIZ_KEY,
                              _external=True), json=payload)

    if not r:
        message = "could not post answer [%s, %s]" % (r.text, r.status_code)
        print(message)
        return

    return payload


def get_next_word(wordlist_ids, queries):
    # wordlist_ids and queries are both lists and may be empty
    global QUIZ_KEY

    url = url_for('api_quiz.get_word_to_test',
                  wordlist_id=wordlist_ids,
                  quiz_key=QUIZ_KEY,
                  query=queries,
                  _external=True)

    while True:
        r = requests.get(url)
        if not r:
            print("get_word_to_test failed:  [%s - %s]" % (r.text, r.status_code))
            break

        attr_to_test = r.json()
        if not attr_to_test:
            print("attr_to_test is bupkus")
            break

        yield attr_to_test
        continue

    yield None


def boring_next_word():
    # for testing
    yield None


def make_triple(function, *args, **kwargs):
    return (function, args, kwargs)


def get_generating_function():
    # returns a triple containing (function, args, kwargs)
    # depending on how the app state has been set

    global WORDLISTS
    global QUERIES
    global TAGS

    wordlist_ids = list(WORDLISTS.keys())
    queries = list(QUERIES)
    tags = list(TAGS)

    return make_triple(get_next_word, wordlist_ids, queries)


def quiz_definitions():
    global WORDLISTS
    global QUERIES
    global TAGS
    global COUNTER
    global WORDS_MISSED
    global QUIZ_KEY

    wordlist_ids = list(WORDLISTS.keys())
    queries = list(QUERIES)

    # reset counter
    # while generator.next()
    #     bump counter
    #     show word
    #     prompt loop
    #     show answer
    #     prompt for correct
    #     post result

    COUNTER = 0
    for attr_to_test in get_next_word(wordlist_ids, queries):
        if not attr_to_test:
            print("es gibt keine Welten mehr zu erobern")
            break

        COUNTER += 1

        if 'article' in attr_to_test:
            print("[%s] %s %s" % (COUNTER, attr_to_test['article'], attr_to_test['word']))
        else:
            print("[%s] %s" % (COUNTER, attr_to_test['word']))

        prompt = "----- [hit return for next one, q to stop] -----> "
        answer = input(prompt).strip().casefold()
        if answer == 'q':
            break


CALLBACKS = {
    'l': {
        'tagline': 'select lists',
        'display_order': 0,
        'callback': select_lists
    },
    'tags': {  # this won't appear in the main menu unless WORDLISTS has exactly one id in it.
        'tagline': 'select tags',
        'display_order': 2,
        'callback': select_tags
    },
    'k': {
        'tagline': 'select queries',
        'display_order': 5,
        'callback': select_queries
    },
    'go': {
        'tagline': 'start quiz',
        'display_order': 10,
        'callback': quiz_definitions
    },
    'f': {
        'tagline': 'show missed words',
        'display_order': 15,
        'callback': unimplemented
    },
    'r': {
        'tagline': 'quiz missed words',
        'display_order': 20,
        'callback': unimplemented
    },
    'report': {
        'tagline': 'report',
        'display_order': 25,
        'callback': unimplemented
    },
    'status': {
        'tagline': 'show app status',
        'display_order': 30,
        'callback': status
    },
    'h': {
        'tagline': 'this menu',
        'display_order': 35,
        'callback': main_menu
    },
    'reset': {
        'tagline': 'reset',
        'display_order': 36,
        'callback': reset
    },
    'q': {
        'tagline': 'quit',
        'display_order': 40,
        'callback': quit_program
    },
}


@bp.cli.command('quiz_defs_2')
def quiz_words():
    while True:
        callback = main_menu()

        if callback == quit_program:
            break

        if callback == main_menu:
            continue

        callback()

    callback()

