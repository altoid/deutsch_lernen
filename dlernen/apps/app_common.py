import requests
from dlernen import config
from pprint import pprint


def get_next_word_to_test(wordlist_ids, quiz_key):
    url = "%s/api/quiz_data/%s" % (config.Config.DB_URL, quiz_key)
    if wordlist_ids:
        wordlist_ids = ','.join(list(map(str, wordlist_ids)))
        url = "%s?wordlist_id=%s" % (url, wordlist_ids)

    r = requests.get(url)
    quiz_data = r.json()
    if not quiz_data:
        return None

    # dig the word_ids out of the result and then find the articles for each word that is a noun.
    word_ids = [x['word_id'] for x in quiz_data]
    url = "%s/api/words" % config.Config.DB_URL
    payload = {
        "word_ids": word_ids
    }
    r = requests.put(url, json=payload)
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
