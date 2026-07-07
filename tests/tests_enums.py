import unittest
from dlernen import create_app
from dlernen.api_quiz import Selector


class QuizKey(unittest.TestCase):
    # make sure dynamically-created QuizKey Enum class is well-behaved

    app = None
    app_context = None
    client = None
    QuizKey = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.QuizKey = cls.app.extensions.get('QuizKey')
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test1(self):
        self.assertEqual('genders', self.QuizKey.GENDERS)

    def test2(self):
        self.assertTrue(self.QuizKey.DEFINITIONS in self.QuizKey)

    def test3(self):
        self.assertTrue('past_participle' in self.QuizKey)

    def test4(self):
        self.assertEqual(self.QuizKey.DEFINITIONS.quiz_id, self.QuizKey.get_id('definitions'))

    def test5(self):
        with self.assertRaises(ValueError):
            x = self.QuizKey.get_id('theudietuhnid')


class SelectorTests(unittest.TestCase):
    # make sure dynamically-created Selector Enum class is well-behaved

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

    def test1(self):
        self.assertTrue('random' in Selector)

    def test2(self):
        self.assertEqual('random', str(Selector.RANDOM))

    def test3(self):
        self.assertEqual('oldest_first', Selector.OLDEST_FIRST)

    def test4(self):
        self.assertTrue(Selector.OLDEST_FIRST, Selector.DEFAULT)

    def test6(self):
        self.assertTrue(Selector.RARE in Selector)


class PosName(unittest.TestCase):
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


class AttrKey(unittest.TestCase):
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

    def test4(self):
        self.assertEqual(self.AttrKey.DEFINITION.attribute_id, self.AttrKey.get_id('definition'))

    def test5(self):
        with self.assertRaises(ValueError):
            x = self.AttrKey.get_id('theudietuhnid')
