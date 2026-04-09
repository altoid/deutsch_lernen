import unittest
import jsonschema
from dlernen import create_app
from dlernen.dlernen_json_schema import get_validator, \
    QUIZ_RESPONSE_SCHEMA, \
    WORD_RESPONSE_SCHEMA, \
    WORD_RESPONSE_ARRAY_SCHEMA
from flask import url_for
import json
from pprint import pprint
from mysql.connector import connect
from contextlib import closing


class APITests(unittest.TestCase):
    app = None
    app_context = None
    client = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test_real_quiz_data(self):
        url = url_for('api_quiz.get_word_to_test', quiz_key='plurals')
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        quiz_data = json.loads(r.data)

        get_validator(QUIZ_RESPONSE_SCHEMA).validate(quiz_data)

    def test_get_word_by_word_exact(self):
        url = url_for('api_word.get_word', word='verderben')
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        results = json.loads(r.data)
        self.assertGreater(len(results), 0)
        get_validator(WORD_RESPONSE_ARRAY_SCHEMA).validate(results)

    def test_get_word_no_match(self):
        url = url_for('api_word.get_word', word='anehuintaoedhunateohdu')
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_get_word_by_word_partial(self):
        url = url_for('api_word.get_word', word='geh', partial=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        results = json.loads(r.data)
        self.assertGreater(len(results), 0)
        get_validator(WORD_RESPONSE_ARRAY_SCHEMA).validate(results)

    def test_get_words_empty_list_1(self):
        url = url_for('api_words.get_words_from_word_ids')
        payload = {
        }

        r = self.client.put(url, json=payload)
        self.assertEqual(200, r.status_code)
        result = json.loads(r.data)
        self.assertEqual([], result)

    def test_get_words_empty_list_2(self):
        url = url_for('api_words.get_words_from_word_ids')
        payload = {
            "word_ids": []
        }

        r = self.client.put(url, json=payload)
        self.assertEqual(200, r.status_code)
        result = json.loads(r.data)
        self.assertEqual([], result)

    def test_all_the_things(self):
        from dlernen.dlernen_json_schema import get_validator, WORDLIST_METADATA_RESPONSE_ARRAY_SCHEMA

        with closing(connect(**self.app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            wordlist_ids = [
                5528,  # smart
                45,  # empty
                85,  # standard
                132,  # smart
                126,  # smart
            ]

            args = ','.join(['%s'] * len(wordlist_ids))

            sql = """
            with wordlist_counts as
            (
            select wordlist_id, sum(c) lcount from
            (
                select wordlist_id, count(*) c
                from wordlist_word
                group by wordlist_id
            ) a
            group by wordlist_id
            )
            select name, id wordlist_id, ifnull(lcount, 0) count, sqlcode, citation
            from wordlist
            left join wordlist_counts wc on wc.wordlist_id = wordlist.id
            where wordlist.id in (%(args)s)
            """ % {'args': args}

            cursor.execute(sql, wordlist_ids)
            metadata_rows = cursor.fetchall()
            # pprint(metadata_rows)

            # the connector is returning the count as a Decimal, have to convert it to int
            for r in metadata_rows:
                r['count'] = int(r['count'])

            smartlists = list(filter(lambda x: x['sqlcode'] is not None, metadata_rows))
            pprint(smartlists)

            # my_sqlcode_thing = [
            #     {
            #         'wordlist_id': 666,
            #         'sqlcode': """select id word_id from word where word = 'phonyword'"""
            #     },
            #     {
            #         'wordlist_id': 555,
            #         'sqlcode': """select id word_id from word where word = 'fartface'"""
            #     },
            # ]

            # construct a single sql query from all of the sqlcodes, which will give the word counts by wordlist_id
            # as fetched by the sqlcodes.

            selectors = [
                """
                select %(wordlist_id)s wordlist_id, word_id from (
                %(sqlcode)s
                ) a%(wordlist_id)s 
                """ % {
                    'wordlist_id': x['wordlist_id'],
                    'sqlcode': x['sqlcode']
                }
                for x in smartlists
            ]

            # sql = """
            # with omg as (
            # select 666 wordlist_id, word_id from
            # (
            # select id word_id from word where word = 'phonyword'
            # ) a666
            # UNION
            # select 555 wordlist_id, word_id from
            # (
            # select id word_id from word where word = 'fartface'
            # ) a555
            # )
            # select wordlist_id, count(*) count
            # from omg
            # group by wordlist_id
            # """

            # pprint(selectors)

            sql = ' UNION '.join(selectors)
            sql = """
            with omg as
            (
            %(sql)s
            )
            select wordlist_id, count(*) count
            from omg
            group by wordlist_id
            """ % {'sql': sql}

            cursor.execute(sql)
            smartlist_counts = cursor.fetchall()
            pprint(smartlist_counts)

            wordlist_id_to_metadata = {x['wordlist_id']: x for x in metadata_rows}

            for x in smartlist_counts:
                wordlist_id_to_metadata[x['wordlist_id']]['count'] = x['count']

            result = list(wordlist_id_to_metadata.values())
            for r in result:
                if r['sqlcode']:
                    r['list_type'] = 'smart'
                elif r['count'] > 0:
                    r['list_type'] = 'standard'
                else:
                    r['list_type'] = 'empty'

            pprint(result)

            get_validator(WORDLIST_METADATA_RESPONSE_ARRAY_SCHEMA).validate(result)

