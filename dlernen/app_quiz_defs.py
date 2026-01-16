from flask import Blueprint, url_for
from pprint import pprint
import requests
import click
import random

bp = Blueprint('app_quiz_defs', __name__)

QUIZ_KEY = 'definitions'
WORDLISTS = {}  # maps wordlist_ids to names
QUERIES = []
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
        print("    %s --> %s" % (c, CALLBACKS[c]['tagline']))
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


def select_lists():
    global WORDLISTS
    global TAGS

    wordlist_ids = []
    selection = {}  # list ids to names

    print("""
Enter list ids, c to clear, s to show selection, d when done""")

    while True:
        prompt = '[select lists] ---> '
        answer = input(prompt).strip().lower()
        if not answer:
            continue

        if answer == 'c':
            WORDLISTS.clear()
            TAGS.clear()
            print("selection cleared")
            continue

        if answer == 's':
            if not selection:
                print("no lists selected, defaults to whole dictionary")
            else:
                for k, v in selection.items():
                    print("[%s] - %s" % (k, v))
            continue

        if answer == 'd':
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
Words tested this session:  %s""" % COUNTER)

    print("""
Words missed this session:  %s""" % len(WORDS_MISSED))


def select_queries():
    unimplemented()


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
        'display_order': 1,
        'callback': select_queries
    },
    'g': {
        'tagline': 'start quiz',
        'display_order': 2,
        'callback': unimplemented
    },
    'f': {
        'tagline': 'show missed words',
        'display_order': 3,
        'callback': unimplemented
    },
    'r': {
        'tagline': 'quiz missed words',
        'display_order': 4,
        'callback': unimplemented
    },
    'z': {
        'tagline': 'report',
        'display_order': 5,
        'callback': unimplemented
    },
    's': {
        'tagline': 'status',
        'display_order': 6,
        'callback': status
    },
    'h': {
        'tagline': 'this menu',
        'display_order': 7,
        'callback': main_menu
    },
    'q': {
        'tagline': 'quit',
        'display_order': 8,
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

