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
TAGS = []
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
    options_in_display_order = sorted(CALLBACKS.keys(), key=lambda x: CALLBACKS[x]['display_order'])

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
        print("<< show tags >>")
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


def quiz_definitions():
    unimplemented()


CALLBACKS = {
    'l': {
        'tagline': 'select lists',
        'display_order': 0,
        'callback': select_lists
    },
    'k': {
        'tagline': 'select queries',
        'display_order': 5,
        'callback': select_queries
    },
    'go': {
        'tagline': 'start quiz',
        'display_order': 10,
        'callback': unimplemented
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
        'tagline': 'status',
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

