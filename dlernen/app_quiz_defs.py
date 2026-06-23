from flask import Blueprint, url_for
from pprint import pprint, pformat
import requests
from dlernen.api_quiz import Selector
from dlernen.dlernen_json_schema import ATTRIBUTES

import pickle

bp = Blueprint('app_quiz_defs', __name__)

STATE_FILE = '.quiz_defs'


class AppState(object):
    def __init__(self,
                 quiz_key='definitions',
                 selector=Selector.DEFAULT,
                 wordlists=None,
                 tags=None,
                 words_hinted=None,
                 words_missed=None):
        self.quiz_key = quiz_key
        self.selector = selector

        # dict mapping wordlist_ids to wordlist names.
        if wordlists:
            self.wordlists = wordlists
        else:
            self.wordlists = dict()

        if tags:
            self.tags = tags
        else:
            self.tags = set()

        # word ids for which hints were requested, mapped to corresponding QUIZ_RESPONSE_SCHEMA object.
        if words_hinted:
            self.words_hinted = words_hinted
        else:
            self.words_hinted = {}

        # same, but with word ids for words marked as missed.
        if words_missed:
            self.words_missed = words_missed
        else:
            self.words_missed = {}

        # if false, do not write quiz results to database.
        self.post_scores = False

    def reset(self):
        self.wordlists.clear()
        self.selector = Selector.DEFAULT
        self.tags.clear()
        self.post_scores = False
        self.words_missed.clear()
        self.words_hinted.clear()


APPSTATE = AppState()


#######################################
#
# this is the entry point
#
#
@bp.cli.command('quiz_definitions')
def quiz_words():
    global STATE_FILE
    global APPSTATE

    try:
        with open(STATE_FILE, 'rb') as f:
            APPSTATE = pickle.load(f)
    except FileNotFoundError as e:
        APPSTATE = AppState()

    status()

    while True:
        callback = main_menu()

        if callback == quit_program:
            break

        if callback == main_menu:
            continue

        callback()

    callback()


def unimplemented():
    print("""
    #############################
    #       unimplemented       #
    #############################
    """)


def quit_program():
    global APPSTATE
    global STATE_FILE

    with open(STATE_FILE, 'wb') as f:
        pickle.dump(APPSTATE, f)

    print('bis bald')


def main_menu():
    global APPSTATE

    options_in_display_order = sorted(CALLBACKS.keys(), key=lambda x: CALLBACKS[x]['display_order'])
    if len(APPSTATE.wordlists) != 1:
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


def set_wordlists(given_wordlist_ids):
    # returns a set containing any wordlist_ids that weren't in the database

    global APPSTATE

    unknown_wordlist_ids = set()
    for wl_id in given_wordlist_ids:
        r = requests.get(url_for('api_wordlist.get_metadata',
                                 wordlist_id=wl_id))
        if r.status_code == 404:
            unknown_wordlist_ids.add(wl_id)
            continue

        if not r:
            print(r.text, r.status_code)
            continue

        obj = r.json()

        APPSTATE.wordlists[wl_id] = obj['name']

    return unknown_wordlist_ids


def reset():
    global APPSTATE

    APPSTATE.reset()


def toggle_posting_scores():
    global APPSTATE

    APPSTATE.post_scores = not APPSTATE.post_scores

    print("posting scores is now %s" % ("ON" if APPSTATE.post_scores else "OFF"))


def select_lists():
    global APPSTATE

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
            APPSTATE.wordlists.clear()
            APPSTATE.tags.clear()
            APPSTATE.clear_hinted_and_missed_tags()
            print("selection cleared")
            continue

        if answer == 's':
            if not APPSTATE.wordlists:
                print("no lists selected, defaults to whole dictionary")
            else:
                for k, v in APPSTATE.wordlists.items():
                    print("[%s] - %s" % (k, v))
            continue

        if answer == 'r':
            break

        try:
            wordlist_ids += list(map(int, answer.split()))
        except ValueError as e:
            print("bad dog:  %s" % str(e))
            continue

        unknown_wordlist_ids = set_wordlists(wordlist_ids)
        if unknown_wordlist_ids:
            print("unknown wordlist_ids:  %s" % pformat(set(unknown_wordlist_ids)))

    if APPSTATE.wordlists:
        print("""
lists selected:
""")
        for v in APPSTATE.wordlists.values():
            print(v)
    else:
        print("""
** no lists selected; using entire dictionary **
""")


def status():
    global APPSTATE

    print("""
****************************************
*
*         Status
*
****************************************

""")

    if APPSTATE.post_scores:
        print("""
Scores ARE being posted to the database""")
    else:
        print("""
Scores ARE NOT being posted to the database""")

    print("""
Lists:""")
    if APPSTATE.wordlists:
        for k, v in APPSTATE.wordlists.items():
            print("[%s] - %s" % (k, v))
    else:
        print("** entire dictionary")

    print("""
Tags:""")
    if APPSTATE.tags:
        print("current tags:  %s" % pformat(APPSTATE.tags))
    else:
        print("** no tags")

    print("""
Selector:  %s""" % APPSTATE.selector)

    url = url_for('api_wordlist.get_word_ids_from_wordlists',
                  wordlist_id=list(APPSTATE.wordlists.keys()),
                  tag=list(APPSTATE.tags))
    r = requests.get(url)
    if r:
        obj = r.json()
        print("""
Word count:  %s""" % len(obj['word_ids']))
    else:
        print("could not retrieve word count:  [%s - %s]" % (r.text, r.status_code))

    print("""
Words missed:
""")
    for w in APPSTATE.words_missed.values():
        print("    %s (%s)" % (w['word'], w['pos_name']))

    print("""
Words where hints requested:
""")
    for w in APPSTATE.words_hinted.values():
        print("    %s (%s)" % (w['word'], w['pos_name']))


def clear_hinted_and_missed_tags():
    global APPSTATE

    APPSTATE.clear_hinted_and_missed_tags()


def select_tags():
    global APPSTATE

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
            APPSTATE.tags.clear()
            continue

        if answer == 's':
            print("current tags:  %s" % pformat(APPSTATE.tags))
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            break

        tags = set(answer.split())
        APPSTATE.tags |= tags
        print("current tags:  %s" % pformat(APPSTATE.tags))


def select_selector():
    global APPSTATE

    menu = """
s - show selection
h - show possible selectors
m - show menu
r - return to main menu
or enter selector name
"""

    print(menu)
    print("current selector:  %s" % APPSTATE.selector)

    while True:
        prompt = '[select selector] ---> '
        answer = input(prompt).strip().casefold()
        if not answer:
            continue

        if answer == 's':
            print("selection:  %s" % APPSTATE.selector)
            continue

        if answer == 'h':
            print("possible selectors:")
            for q in Selector:
                print("    %s" % q)
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            if not APPSTATE.selector:
                APPSTATE.selector = Selector.DEFAULT
            break

        if answer not in Selector:
            print("not a valid selector:  %s" % answer)
            continue

        APPSTATE.selector = answer
        print("selection:  %s" % APPSTATE.selector)


def show_missed_words():
    global APPSTATE

    if not APPSTATE.words_missed:
        print("""
    ********************************
    * no words missed this session *
    ********************************
    """)
        return

    print("""
    *****************************
    * words missed this session *
    *****************************
    """)
    for w in APPSTATE.words_missed.values():
        print("    %s (%s)" % (w['word'], w['pos_name']))


def show_hinted_words():
    global APPSTATE

    if not APPSTATE.words_hinted:
        print("""
    ***********************************
    * no hints requested this session *
    ***********************************
    """)
        return

    print("""
    ********************************
    * hints requested this session *
    ********************************
    """)
    for w in APPSTATE.words_hinted.values():
        print("    %s (%s)" % (w['word'], w['pos_name']))


def get_next_word(wordlist_ids, selector):
    # wordlist_ids is a list and may be empty.
    global APPSTATE

    # the quiz api works by getting ALL candidates in one go.  even if it's the whole dictionary.  subsequent calls
    # here (and to similar functions) will just loop over the list forever.

    url = url_for('api_quiz.get_words',
                  wordlist_id=wordlist_ids,
                  quiz_key=APPSTATE.quiz_key,
                  selector=selector)

    r = requests.get(url)
    if r:
        words_to_test = r.json()
        if not words_to_test:
            yield None

        i = 0
        while True:
            yield words_to_test[i]
            i += 1
            i = i % len(words_to_test)

    print("get_words failed:  [%s - %s]" % (r.text, r.status_code))
    yield None


def get_next_word_with_tags(wordlist_id, selector, tags):
    # wordlist_id is a single id, not a list.

    global APPSTATE

    url = url_for('api_quiz.get_words_in_wordlist',
                  wordlist_id=wordlist_id,
                  quiz_key=APPSTATE.quiz_key,
                  selector=selector,
                  tag=tags)

    r = requests.get(url)
    if r:
        words_to_test = r.json()
        if not words_to_test:
            yield None

        i = 0
        while True:
            yield words_to_test[i]
            i += 1
            i = i % len(words_to_test)

    print("get_words_in_wordlist failed:  [%s - %s]" % (r.text, r.status_code))
    yield None


def dummy_get_next_word(wordlist_ids, queries):
    # for testing
    pprint(wordlist_ids)
    pprint(queries)

    yield None


# candidates is a list of QUIZ_RESPONSE_SCHEMA objects.  loop through them ad nauseum
def get_next_word_from_list(candidates):
    if not candidates:
        yield None

    i = 0
    while True:
        yield candidates[i]
        i += 1
        i = i % len(candidates)


def make_triple(function, *args, **kwargs):
    return function, args, kwargs


def quiz_definitions():
    global APPSTATE

    wordlist_ids = list(APPSTATE.wordlists.keys())
    selector = APPSTATE.selector
    tags = list(APPSTATE.tags)

    if len(wordlist_ids) == 1:
        function_and_args = make_triple(get_next_word_with_tags, wordlist_ids[0], selector, tags)
    else:
        function_and_args = make_triple(get_next_word, wordlist_ids, selector)

    quiz_loop(function_and_args)


def quiz_hinted_words():
    global APPSTATE

    function_and_args = make_triple(get_next_word_from_list, list(APPSTATE.words_hinted.values()))

    quiz_loop(function_and_args)


def quiz_missed_words():
    global APPSTATE

    function_and_args = make_triple(get_next_word_from_list, list(APPSTATE.words_missed.values()))

    quiz_loop(function_and_args)


def quiz_loop(generating_function_and_args):
    global APPSTATE

    function, args, kwargs = generating_function_and_args

    count = 1
    for word_to_test in function(*args, **kwargs):
        if not word_to_test:
            print("es gibt keine Welten mehr zu erobern")
            break

        word = "%s %s" % (word_to_test.get('article', ''), word_to_test['word'])
        word = word.strip()
        print("[%s] %s" % (count, word))

        # no need to loop over the attributes.  there's only one we care about.  fish it out.
        defn_attr = list(filter(lambda x: x['attrkey'] == 'definition', word_to_test[ATTRIBUTES]))[0]

        while True:
            prompt = "hit return for answer, r to return to main menu, h for hint:  --> "
            answer = input(prompt).strip().lower()

            if answer.startswith('r'):
                break

            if not answer:
                break

            if answer.startswith('h'):
                APPSTATE.words_hinted[word_to_test['word_id']] = word_to_test

                # show wordlists this word is in.
                r = requests.get(url_for('api_word.get_member_wordlists',
                                         word_id=word_to_test['word_id']))
                if not r:
                    message = "could not get wordlists for word id %s:  [%s, %s]" % (word_to_test['word_id'], r.text,
                                                                                     r.status_code)
                    print(message)
                    return message, r.status_code

                # this is a WORD_WORDLIST_METADATA_MAP_SCHEMA object.
                obj = r.json()

                wordlist_list_obj = obj['wordlist_metadata_list']

                for n in wordlist_list_obj:
                    r = requests.get(url_for('api_wordlist_tag.get_tags',
                                             wordlist_id=n['wordlist_id'],
                                             word_id=word_to_test['word_id']))
                    if not r:
                        message = "could not get tags for word id %s:  [%s, %s]" % (
                            word_to_test['word_id'], r.text,
                            r.status_code)
                        print(message)
                        return message, r.status_code

                    tags_response = r.json()
                    tags = ', '.join(tags_response['tags'])
                    if tags:
                        print("%s [%s:  %s]" % (n['name'], n['wordlist_id'], tags))
                    else:
                        print("%s [%s]" % (n['name'], n['wordlist_id']))

                continue

            print("unknown response:  %s" % answer)

        if answer.startswith('r'):
            break

        print(defn_attr['attrvalue'])

        if APPSTATE.post_scores:
            prompt = "correct? --> "
            answer = input(prompt).strip().lower()

            while len(answer) == 0:
                answer = input(prompt).strip().lower()

            correct = answer.startswith('y')

            payload = {
                "word_id": word_to_test['word_id'],
                "attribute_id": defn_attr['attribute_id'],
                'correct': correct
            }

            r = requests.post(url_for('api_quiz.post_quiz_score',
                                      quiz_key=APPSTATE.quiz_key),
                              json=payload)

            if not r:
                message = "could not post answer [%s, %s]" % (r.text, r.status_code)
                print(message)
                break

            if not correct:
                APPSTATE.words_missed[word_to_test['word_id']] = word_to_test

        count += 1


CALLBACKS = {
    'p': {
        'tagline': 'toggle posting scores',
        'display_order': 0,
        'callback': toggle_posting_scores
    },
    'l': {
        'tagline': 'select lists',
        'display_order': 2,
        'callback': select_lists
    },
    'tags': {  # this won't appear in the main menu unless APPSTATE.wordlists has exactly one id in it.
        'tagline': 'select tags',
        'display_order': 4,
        'callback': select_tags
    },
    'e': {
        'tagline': 'clear missed and hinted tags',
        'display_order': 6,
        'callback': clear_hinted_and_missed_tags,
    },
    'k': {
        'tagline': 'choose selector',
        'display_order': 8,
        'callback': select_selector
    },
    'go': {
        'tagline': 'start quiz',
        'display_order': 10,
        'callback': quiz_definitions
    },
    'f': {
        'tagline': 'show missed words',
        'display_order': 15,
        'callback': show_missed_words
    },
    'r': {
        'tagline': 'quiz missed words',
        'display_order': 20,
        'callback': quiz_missed_words
    },
    'sh': {
        'tagline': 'show words needing hints',
        'display_order': 22,
        'callback': show_hinted_words
    },
    'qh': {
        'tagline': 'quiz words needing hints',
        'display_order': 24,
        'callback': quiz_hinted_words
    },
    'report': {
        'tagline': 'report',
        'display_order': 25,
        'callback': unimplemented
    },
    'status': {
        'tagline': 'show session status',
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
        'display_order': 40,
        'callback': reset
    },
    'q': {
        'tagline': 'quit',
        'display_order': 45,
        'callback': quit_program
    },
}
