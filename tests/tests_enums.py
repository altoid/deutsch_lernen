import unittest
from dlernen import create_app


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

    def test4(self):
        self.assertEqual(self.AttrKey.DEFINITION.attribute_id, self.AttrKey.get_id('definition'))

    def test5(self):
        with self.assertRaises(ValueError):
            x = self.AttrKey.get_id('theudietuhnid')
