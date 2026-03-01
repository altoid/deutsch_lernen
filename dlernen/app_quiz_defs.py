import random

from flask import Blueprint, url_for
from pprint import pprint
import requests
from dlernen import api_quiz
import pickle

bp = Blueprint('app_quiz_defs', __name__)

STATE_FILE = '.quiz_defs'
MISSED_TAG = '__missed'
HINTED_TAG = '__hinted'


class AppState(object):
    def __init__(self,
                 quiz_key='definitions',
                 query='random',
                 wordlists=None,
                 tags=None,
                 hints_requested=None,
                 missed=None):
        self.quiz_key = quiz_key
        self.query = query

        # dict mapping wordlist_ids to wordlist names.
        if wordlists:
            self.wordlists = wordlists
        else:
            self.wordlists = dict()

        if tags:
            self.tags = tags
        else:
            self.tags = set()

        # set of word ids for which hints were requested.
        if hints_requested:
            self.hints_requested = hints_requested
        else:
            self.hints_requested = set()

        # ... and words which were missed.
        if missed:
            self.missed = missed
        else:
            self.missed = set()

        # general-purpose mapping of word ids to word objects, so that we can retrieve word info
        # when we want it.
        self.cache = dict()

        # if false, do not write quiz results to database.
        self.post_scores = False

    def reset(self):
        self.wordlists.clear()
        self.query = 'random'
        self.tags.clear()
        # self.cache.clear()  # no need to flush the cache on reset
        self.post_scores = False

        self.clear_hinted_and_missed_tags()
        self.load_hinted_and_missed_tags()

    def get_word_info(self, word_id):
        if word_id not in self.cache:
            r = requests.get(url_for('api_word.get_word_by_id', word_id=word_id))
            obj = r.json()
            self.cache[word_id] = obj
        return self.cache[word_id]

    def clear_hinted_and_missed_tags(self):
        # clear the missed and hinted word id sets, but do not mess with the hinted and missed tags.

        self.missed.clear()
        self.hints_requested.clear()

    def load_hinted_and_missed_tags(self):
        # client should clear hinted and missed sets first.

        ids = list(self.wordlists.keys())
        if ids:
            r = requests.get(url_for('api_words.get_words', tag=[MISSED_TAG], wordlist_id=ids))
            obj = r.json()
            for w in obj:
                self.cache[w['word_id']] = w
                self.missed.add(w['word_id'])

            r = requests.get(url_for('api_words.get_words', tag=[HINTED_TAG], wordlist_id=ids))
            obj = r.json()
            for w in obj:
                self.cache[w['word_id']] = w
                self.hints_requested.add(w['word_id'])


APPSTATE = AppState()


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
        r = requests.get(url_for('api_wordlist.get_wordlist_metadata',
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
    if not APPSTATE.post_scores and APPSTATE.query == 'oldest_first':
        APPSTATE.query = 'random'


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

        print("list_ids:  ", end=' ')
        pprint(set(APPSTATE.wordlists.keys()))

        if unknown_wordlist_ids:
            print("unknown wordlist_ids:  ", end=' ')
            pprint(set(unknown_wordlist_ids))

    APPSTATE.load_hinted_and_missed_tags()


def status():
    global APPSTATE

    pprint(APPSTATE.cache)
    pprint(APPSTATE.missed)
    pprint(APPSTATE.hints_requested)

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
        print("current tags:  ", end=' ')
        pprint(APPSTATE.tags)
    else:
        print("** no tags")

    print("""
Query:  %s""" % APPSTATE.query)

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
Words missed this session:
""")
    for w_id in APPSTATE.missed:
        w = APPSTATE.get_word_info(w_id)
        print("    %s (%s)" % (w['word'], w['pos_name']))

    print("""
Words where hints requested:
""")
    for w_id in APPSTATE.hints_requested:
        w = APPSTATE.get_word_info(w_id)
        print("    %s (%s)" % (w['word'], w['pos_name']))


def clear_hinted_and_missed_tags():
    global APPSTATE

    ids = list(APPSTATE.wordlists.keys())

    # clear the __missed and __hinted tags from appstate word lists
    r = requests.delete(url_for('api_wordlist_tag.delete_tag',
                                wordlist_id=ids,
                                tag=MISSED_TAG))

    r = requests.delete(url_for('api_wordlist_tag.delete_tag',
                                wordlist_id=ids,
                                tag=HINTED_TAG))

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
            print("current tags:  ", end=' ')
            pprint(APPSTATE.tags)
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            break

        tags = set(answer.split())
        APPSTATE.tags |= tags
        print("current tags:  ", end=' ')
        pprint(APPSTATE.tags)


def select_query():
    global APPSTATE

    menu = """
c - clear selection
s - show selection
q - show possible queries
m - show menu
r - return to main menu
or enter query name
"""

    print(menu)
    print("current query:  %s" % APPSTATE.query)
    possible_queries = set(api_quiz.DEFINED_QUERIES.keys())
    possible_queries.add('random')
    if not APPSTATE.post_scores:
        # posting scores changes the what the oldest is (by converting the oldest
        # to the newest, giving us a new oldest).  if we AREN'T posting scores, the oldest
        # never changes.  so remove this as an option.
        possible_queries.remove('oldest_first')

    while True:
        prompt = '[select query] ---> '
        answer = input(prompt).strip().casefold()
        if not answer:
            continue

        if answer == 'c':
            APPSTATE.query = None
            print("selection cleared")
            continue

        if answer == 's':
            print("selection:  %s" % APPSTATE.query)
            continue

        if answer == 'q':
            print("possible queries:")
            for q in possible_queries:
                print("    %s" % q)
            continue

        if answer == 'm':
            print(menu)
            continue

        if answer == 'r':
            if not APPSTATE.query:
                APPSTATE.query = 'oldest_first'
            break

        if answer not in possible_queries:
            print("not a valid query:  %s" % answer)
            continue

        APPSTATE.query = answer
        print("selection:  %s" % APPSTATE.query)


def show_missed_words():
    global APPSTATE

    if not APPSTATE.missed:
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
    for w_id in APPSTATE.missed:
        w = APPSTATE.get_word_info(w_id)
        print("    %s (%s)" % (w['word'], w['pos_name']))


def show_hinted_words():
    global APPSTATE

    if not APPSTATE.hints_requested:
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
    for w_id in APPSTATE.hints_requested:
        w = APPSTATE.get_word_info(w_id)
        print("    %s (%s)" % (w['word'], w['pos_name']))


def get_next_word(wordlist_ids, query):
    # wordlist_ids and query are both lists and may be empty
    global APPSTATE

    url = url_for('api_quiz.get_word_to_test',
                  wordlist_id=wordlist_ids,
                  quiz_key=APPSTATE.quiz_key,
                  query=query)

    while True:
        r = requests.get(url)
        if not r:
            print("get_word_to_test failed:  [%s - %s]" % (r.text, r.status_code))
            break

        attrs_to_test = r.json()
        if not attrs_to_test:
            print("attrs_to_test is bupkus")
            break

        yield attrs_to_test[0]
        continue

    yield None


def get_next_word_with_tags(wordlist_id, query, tags):
    # wordlist_id is a single id, not a list.

    global APPSTATE

    url = url_for('api_quiz.get_word_to_test_single_wordlist',
                  wordlist_id=wordlist_id,
                  tag=tags,
                  quiz_key=APPSTATE.quiz_key,
                  query=query)

    while True:
        r = requests.get(url)
        if not r:
            print("get_word_to_test_single_wordlist failed:  [%s - %s]" % (r.text, r.status_code))
            break

        attrs_to_test = r.json()
        if not attrs_to_test:
            print("attrs_to_test is bupkus")
            break

        yield attrs_to_test[0]
        continue

    yield None


def dummy_get_next_word(wordlist_ids, queries):
    # for testing
    pprint(wordlist_ids)
    pprint(queries)

    yield None


def get_next_saved_word(saved_word_ids, word_ids_to_attrs):
    if not saved_word_ids:
        yield None

    i = 0
    while True:
        yield word_ids_to_attrs[saved_word_ids[i]]
        i += 1
        i = i % len(saved_word_ids)


def make_triple(function, *args, **kwargs):
    return function, args, kwargs


def decorate_if_noun(word_object):
    # if this is a noun, add its article to the object.
    url = url_for('api_word.get_word_by_id', word_id=word_object['word_id'])

    r = requests.get(url)
    # if not r, deal with it later, i'm tired.

    obj = r.json()
    if obj['pos_name'].casefold() == 'noun':
        article = list(filter(lambda x: x['attrkey'] == 'article', obj['attributes']))
        word_object['article'] = article[0]['attrvalue']

    return word_object


def get_random_next_word(wordlist_ids, tags):
    r = requests.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                             wordlist_id=wordlist_ids,
                             tag=tags))
    obj = r.json()
    word_ids = obj['word_ids']
    random.shuffle(word_ids)  # shuffle in place

    word_ids_to_attrs = {}
    i = 0
    while True:
        if word_ids[i] not in word_ids_to_attrs:
            url = url_for('api_quiz.get_all_attr_values_for_quiz',
                          quiz_key=APPSTATE.quiz_key,
                          word_id=word_ids[i])
            r = requests.get(url)
            obj = r.json()
            word_ids_to_attrs[word_ids[i]] = decorate_if_noun(obj[0])

        yield word_ids_to_attrs[word_ids[i]]

        i += 1
        i = i % len(word_ids)


def tag_word(word_id, tag):
    # for each wordlist in the app state, affix the HINTED tag to the word.
    # we will get a 400 if the word_id is not in a list, but we will ignore that condition.

    global APPSTATE

    for wordlist_id in APPSTATE.wordlists:
        r = requests.post(url_for('api_wordlist_tag.add_tags',
                                  wordlist_id=wordlist_id,
                                  word_id=word_id),
                          json=[tag])

        if r.status_code == 400:
            pass


def tag_hinted_word(word_id):
    tag_word(word_id, HINTED_TAG)


def tag_missed_word(word_id):
    tag_word(word_id, MISSED_TAG)


def quiz_definitions():
    global APPSTATE

    wordlist_ids = list(APPSTATE.wordlists.keys())
    query = APPSTATE.query
    tags = list(APPSTATE.tags)

    if APPSTATE.query == 'random':
        function_and_args = make_triple(get_random_next_word, wordlist_ids, tags)
    elif len(wordlist_ids) == 1:
        function_and_args = make_triple(get_next_word_with_tags, wordlist_ids[0], query, tags)
    else:
        function_and_args = make_triple(get_next_word, wordlist_ids, query)

    quiz_loop(function_and_args)


def quiz_hinted_words():
    global APPSTATE

    hinted_word_ids = list(APPSTATE.hints_requested)
    word_ids_to_attrs = {}
    for word_id in hinted_word_ids:
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key=APPSTATE.quiz_key,
                      word_id=word_id)
        r = requests.get(url)
        obj = r.json()
        word_ids_to_attrs[word_id] = decorate_if_noun(obj[0])

    function_and_args = make_triple(get_next_saved_word, hinted_word_ids, word_ids_to_attrs)

    quiz_loop(function_and_args)


def quiz_missed_words():
    global APPSTATE

    word_ids_to_attrs = {}
    for word_id in APPSTATE.missed:
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key=APPSTATE.quiz_key,
                      word_id=word_id)
        r = requests.get(url)
        obj = r.json()
        word_ids_to_attrs[word_id] = decorate_if_noun(obj[0])

    function_and_args = make_triple(get_next_saved_word, APPSTATE.missed, word_ids_to_attrs)

    quiz_loop(function_and_args)


def quiz_loop(generating_function_and_args):
    global APPSTATE

    function, args, kwargs = generating_function_and_args

    count = 1
    for attr_to_test in function(*args, **kwargs):
        if not attr_to_test:
            print("es gibt keine Welten mehr zu erobern")
            break

        if 'article' in attr_to_test:
            print("[%s] %s %s" % (count, attr_to_test['article'], attr_to_test['word']))
        else:
            print("[%s] %s" % (count, attr_to_test['word']))

        while True:
            prompt = "hit return for answer, r to return to main menu, h for hint:  --> "
            answer = input(prompt).strip().lower()

            if answer.startswith('r'):
                break

            if not answer:
                break

            if answer.startswith('h'):
                APPSTATE.hints_requested.add(attr_to_test['word_id'])

                # show wordlists this word is in.
                r = requests.get(url_for('api_wordlists.get_wordlists_by_word_id',
                                         word_id=attr_to_test['word_id']))
                if not r:
                    message = "could not get wordlists for word id %s:  [%s, %s]" % (attr_to_test['word_id'], r.text,
                                                                                     r.status_code)
                    print(message)
                    return message, r.status_code

                obj = r.json()
                for n in obj:
                    r = requests.get(url_for('api_wordlist_tag.get_tags',
                                             wordlist_id=n['wordlist_id'],
                                             word_id=attr_to_test['word_id']))
                    if not r:
                        message = "could not get tags for word id %s:  [%s, %s]" % (
                            attr_to_test['word_id'], r.text,
                            r.status_code)
                        print(message)
                        return message, r.status_code

                    tags_response = r.json()
                    tags = ', '.join(tags_response['tags'])
                    if tags:
                        print("%s [%s:  %s]" % (n['name'], n['wordlist_id'], tags))
                    else:
                        print("%s [%s]" % (n['name'], n['wordlist_id']))

                tag_hinted_word(attr_to_test['word_id'])
                APPSTATE.missed.add(attr_to_test['word_id'])
                continue

            print("unknown response:  %s" % answer)

        if answer.startswith('r'):
            break

        print(attr_to_test['attrvalue'])

        if APPSTATE.post_scores:
            prompt = "correct? --> "
            answer = input(prompt).strip().lower()

            while len(answer) == 0:
                answer = input(prompt).strip().lower()

            correct = answer.startswith('y')

            payload = {
                "quiz_id": attr_to_test['quiz_id'],
                "word_id": attr_to_test['word_id'],
                "attribute_id": attr_to_test['attribute_id'],
                'correct': correct
            }

            r = requests.post(url_for('api_quiz.post_quiz_answer',
                                      quiz_key=APPSTATE.quiz_key),
                              json=payload)

            if not r:
                message = "could not post answer [%s, %s]" % (r.text, r.status_code)
                print(message)
                break

            if not correct:
                tag_missed_word(attr_to_test['word_id'])
                APPSTATE.missed.add(attr_to_test['word_id'])

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
        'tagline': 'select query',
        'display_order': 8,
        'callback': select_query
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
        'display_order': 36,
        'callback': reset
    },
    'q': {
        'tagline': 'quit',
        'display_order': 40,
        'callback': quit_program
    },
}


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
