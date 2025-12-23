import unittest
from dlernen import app_urmverb, create_app
import random
import string


class TestURMVerb(unittest.TestCase):
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

    irregular_verbs = [
        'abschaffen',
        'anstoßen',
        'ausgeben',
        'aushalten',
        'backen',
        'befehlen',
        'begießen',
        'beginnen',
        'begreifen',
        'beißen',
        'beladen',
        'bergen',
        'bersten',
        'beschreiben',
        'betrügen',
        'bewegen',
        'biegen',
        'bieten',
        'binden',
        'bitten',
        'blasen',
        'bleiben',
        'bleichen',
        'braten',
        'brechen',
        'bringen',
        'denken',
        'dingen',
        'dreschen',
        'dringen',
        'dürfen',
        'einfallen',
        'einladen',
        'empfangen',
        'empfehlen',
        'empfinden',
        'erschrecken',
        'erwerben',
        'erwägen',
        'essen',
        'fahren',
        'fallen',
        'fangen',
        'fechten',
        'finden',
        'flechten',
        'fliegen',
        'fliehen',
        'fließen',
        'fressen',
        'frieren',
        'geben',
        'gebären',
        'gedeihen',
        'gehen',
        'gelingen',
        'gelten',
        'genesen',
        'genießen',
        'geraten',
        'geschehen',
        'gewinnen',
        'gießen',
        'gleichen',
        'gleiten',
        'greifen',
        'gären',
        'haben',
        'halten',
        'hauen',
        'heben',
        'heißen',
        'helfen',
        'klimmen',
        'klingen',
        'kommen',
        'kriechen',
        'laden',
        'lassen',
        'laufen',
        'leiden',
        'leihen',
        'lesen',
        'liegen',
        'lügen',
        'meiden',
        'melken',
        'messen',
        'nehmen',
        'pfeifen',
        'pflegen',
        'pflügen',
        'quellen',
        'raten',
        'reiben',
        'reißen',
        'riechen',
        'ringen',
        'rufen',
        'saufen',
        'saugen',
        'schaffen',
        'scheiden',
        'scheinen',
        'schelten',
        'schieben',
        'schießen',
        'schlafen',
        'schlagen',
        'schleichen',
        'schleifen',
        'schleißen',
        'schließen',
        'schlingen',
        'schmeißen',
        'schmelzen',
        'schneiden',
        'schreiben',
        'schreien',
        'schreiten',
        'schweigen',
        'schwellen',
        'schwimmen',
        'sehen',
        'sein',
        'senden',
        'sieden',
        'singen',
        'sinken',
        'sinnen',
        'sitzen',
        'speien',
        'sprechen',
        'sprießen',
        'springen',
        'stechen',
        'stehen',
        'stehlen',
        'steigen',
        'sterben',
        'stoßen',
        'streichen',
        'streiten',
        'tragen',
        'treffen',
        'treiben',
        'triefen',
        'trinken',
        'tun',
        'unterstreichen',
        'verbergen',
        'verderben',
        'vergessen',
        'verlassen',
        'verlaufen',
        'verlieren',
        'vermeiden',
        'verschwinden',
        'vertragen',
        'wachsen',
        'waschen',
        'weichen',
        'weisen',
        'wenden',
        'werben',
        'werden',
        'werfen',
        'wiegen',
        'wissen',
        'ziehen',
        'zwingen',
    ]

    modal_verbs = [
        'dürfen',
        'können',
        'mögen',
        'müssen',
        'sollen',
        'wollen'
    ]
    regular_verbs = [
        'abstellen',
    ]

    not_verbs = [
        'jedenfalls',
    ]

    misfits = [
        ''.join(random.choices(string.ascii_lowercase, k=10)),  # not in the dictionary, hopefully
        'verbnosps',  # fake word created for this test.
        'verbnotps',  # ditto
    ]

    def test_sollen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('sollen'))

    def test_bringen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('bringen'))

    def test_bewegen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('bewegen'))

    def test_hauen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('hauen'))

    def test_pflegen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('pflegen'))

    def test_triefen(self):
        with self.app.test_request_context():
            self.assertTrue(app_urmverb.is_irregular_verb('triefen'))

    def test_irregular_verbs(self):
        with self.app.test_request_context():
            for verb in self.irregular_verbs:
                with self.subTest(verb=verb):
                    self.assertTrue(app_urmverb.is_irregular_verb(verb))

    def test_modal_verbs(self):
        with self.app.test_request_context():
            for verb in self.modal_verbs:
                with self.subTest(verb=verb):
                    self.assertTrue(app_urmverb.is_irregular_verb(verb))

    def test_regular_verbs(self):
        with self.app.test_request_context():
            for verb in self.regular_verbs:
                with self.subTest(verb=verb):
                    self.assertFalse(app_urmverb.is_irregular_verb(verb))

    def test_not_verbs(self):
        with self.app.test_request_context():
            for verb in self.not_verbs:
                with self.subTest(verb=verb):
                    self.assertIsNone(app_urmverb.is_irregular_verb(verb))

    def test_misfits(self):
        with self.app.test_request_context():
            for verb in self.not_verbs:
                with self.subTest(verb=verb):
                    self.assertIsNone(app_urmverb.is_irregular_verb(verb))

