import requests
from flask import url_for
from pprint import pprint

# FIXME - properly handle the return values of requests.get/put


def get_next_word_to_test(wordlist_ids, quiz_key):
    if wordlist_ids:
        wordlist_ids = ','.join(list(map(str, wordlist_ids)))

    url = url_for('api_quiz.quiz_data', quiz_key=quiz_key, wordlist_ids=wordlist_ids, _external=True)

    r = requests.get(url)
    quiz_data = r.json()
    if not quiz_data:
        return None

    # dig the word_ids out of the result and then find the articles for each word that is a noun.
    # FIXME - why TF are we doing this?
    word_ids = [x['word_id'] for x in quiz_data]
    payload = {
        "word_ids": word_ids
    }
    r = requests.put(url_for('api_word.get_words', _external=True), json=payload)
    word_attributes = r.json()

    # enrich the quiz_data by adding the articles
    word_id_to_article = {}
    for wa in word_attributes:
        for a in wa['attributes']:
            if a['attrkey'] == 'article':
                word_id_to_article[wa['word_id']] = a['attrvalue']

    for qd in quiz_data:
        if qd['word_id'] in word_id_to_article:
            qd['article'] = word_id_to_article[qd['word_id']]

    return quiz_data[0]
