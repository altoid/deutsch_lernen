from flask import Blueprint, url_for
from pprint import pprint
import requests
import click
import random

bp = Blueprint('app_quiz_defs', __name__)

QUIZ_KEY = 'definitions'
WORDLISTS = []
QUERIES = []
TAGS = []
COUNTER = 0
WORDS_MISSED = {}


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
    wordlist_ids = []
    selection = {}  # list ids to names

    print("""
Enter list ids, c to clear, s to show selection, d when done""")

    while True:
        prompt = '---> '
        answer = input(prompt).strip().lower()
        if not answer:
            continue

        if answer == 'c':
            WORDLISTS.clear()
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
            WORDLISTS = list(selection.keys())
            break

        try:
            wordlist_ids += list(map(int, answer.split()))
            print("list_ids", end=' ')
            pprint(wordlist_ids)
        except ValueError as e:
            print("bad dog")
            continue


def status():
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
        print("<< show word lists here >>")
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

