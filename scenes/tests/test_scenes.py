"""Testing code for the scenes package, unit-testing only."""

import pickle
import unittest
import xml.etree.ElementTree as ETree

from scenes import collins, lex, scenes
from ucca import convert
from ucca.tests.test_ucca import TestUtil


class ScenesTests(unittest.TestCase):

    def test_possible_scenes(self):
        """Tests that the API isn't broken, not validity of the result."""
        elem = TestUtil.load_xml('test_files/site3.xml')
        passage = convert.from_site(elem)
        scenes.extract_possible_scenes(passage)

    def test_extract_head(self):
        """Tests that the API isn't broken, not validity of the result."""
        passage = TestUtil.create_passage()
        for x in scenes.extract_possible_scenes(passage):
            scenes.extract_head(x)


class CollinsTests(unittest.TestCase):

    def test_basic_usage(self):
        with open("test_files/collins-sample.pickle", "rb") as f:
            raw_dict = pickle.load(f)
        coldict = collins.CollinsDictionary(raw_dict)
        self.assertSequenceEqual(coldict.by_key('aaaaaa'), [])
        self.assertEqual(len(coldict.by_key('apart')), 2)
        self.assertEqual(len(coldict.by_form('droughts')), 1)
        self.assertEqual(len(coldict.by_form('drove')), 2)
        self.assertEqual(len(coldict.by_stem('abort')), 3)


class LexTests(unittest.TestCase):

    @unittest.skip
    def test_dixon(self):
        with open("test_files/dixon-verbs.xml") as f:
            root = ETree.ElementTree().parse(f)
        dixon = lex.DixonVerbs(root)
        self.assertSequenceEqual(dixon.by_phrase('get'),
                                 ['Primary-A:GIVING:OWN',
                                  'Secondary-C:MAKING:MAIN'])
        self.assertDictEqual(dixon.by_verb('get'),
                             {'get to': ['Secondary-A:SEMI-MODAL:MAIN'],
                              'get': ['Primary-A:GIVING:OWN',
                                      'Secondary-C:MAKING:MAIN']})
        self.assertDictEqual(dixon.by_stem('hurri'),
                             {'hurry': ['Secondary-A:HURRYING:MAIN']})
