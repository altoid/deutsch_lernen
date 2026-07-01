import unittest
from dlernen import create_app
from flask import url_for
import json
from pprint import pprint


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

    def test_nothing(self):
        # don't do anything, just make sure setup and teardown work
        pass

    def test_pos_structure(self):
        url = url_for('api_pos.get_pos')
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

    def test_bullshit_wordid(self):
        url = url_for('api_pos.get_pos_for_word_id', word_id=83674587)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

        obj = json.loads(r.data)

        self.assertEqual(0, len(obj))


class APIPosName(unittest.TestCase):
    # make sure dynamically-created POSName Enum class is well-behaved

    app = None
    app_context = None
    client = None
    POSName = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.POSName = cls.app.extensions.get('POSName')
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test1(self):
        self.assertEqual('Noun', self.POSName.NOUN)

    def test2(self):
        self.assertTrue(self.POSName.SEPARABLE_PREFIX in self.POSName)

    def test3(self):
        self.assertTrue('Separable_Prefix' in self.POSName)


class APIAttrKey(unittest.TestCase):
    # make sure dynamically-created AttrKey Enum class is well-behaved

    app = None
    app_context = None
    client = None
    AttrKey = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.AttrKey = cls.app.extensions.get('AttrKey')
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test1(self):
        self.assertEqual('article', self.AttrKey.ARTICLE)

    def test2(self):
        self.assertTrue(self.AttrKey.DEFINITION in self.AttrKey)

    def test3(self):
        self.assertTrue('past_participle' in self.AttrKey)


