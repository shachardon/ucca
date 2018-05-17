import xml.etree.ElementTree as ETree

from ucca import layer0, layer1, convert
from .conftest import load_xml

"""Tests convert module correctness and API."""


def _test_edges(self, node, tags):
    """Tests that the node edge tags and number match tags argument."""
    self.assertEqual(len(node), len(tags))
    for edge, tag in zip(node, tags):
        self.assertEqual(edge.tag, tag)


def _test_terms(self, node, terms):
    """Tests that node contain the terms given, and only them."""
    for edge, term in zip(node, terms):
        self.assertEqual(edge.tag, layer1.EdgeTags.Terminal)
        self.assertEqual(edge.child, term)


def test_site_terminals(self):
    elem = load_xml("test_files/site1.xml")
    passage = convert.from_site(elem)
    terms = passage.layer(layer0.LAYER_ID).all

    self.assertEqual(passage.ID, "118")
    self.assertEqual(len(terms), 15)

    # There are two punctuation signs (dots, positions 5 and 11), which
    # also serve as paragraph end points. All others are words whose text
    # is their positions, so test that both text, punctuation (yes/no)
    # and paragraphs are converted correctly
    for i, t in enumerate(terms):
        # i starts in 0, positions at 1, hence 5,11 ==> 4,10
        if i in (4, 10):
            self.assertTrue(t.text == "." and t.punct is True)
        else:
            self.assertTrue(t.text == str(i + 1) and t.punct is False)
        if i < 5:
            par = 1
        elif i < 11:
            par = 2
        else:
            par = 3
        self.assertEqual(t.paragraph, par)


def test_site_simple(self):
    elem = load_xml("test_files/site2.xml")
    passage = convert.from_site(elem)
    terms = passage.layer(layer0.LAYER_ID).all
    l1 = passage.layer("1")

    # The Terminals in the passage are just like in test_site_terminals,
    # with this layer1 hierarchy: [[1 C] [2 E] L] [3 4 . H]
    # with the linker having a remark and the parallel scene is uncertain
    head = l1.heads[0]
    self.assertEqual(len(head), 12)  # including all "unused" terminals
    self.assertEqual(head[9].tag, layer1.EdgeTags.Linker)
    self.assertEqual(head[10].tag, layer1.EdgeTags.ParallelScene)
    linker = head.children[9]
    self._test_edges(linker, [layer1.EdgeTags.Center,
                              layer1.EdgeTags.Elaborator])
    self.assertTrue(linker.extra["remarks"], '"remark"')
    center = linker.children[0]
    elab = linker.children[1]
    self._test_terms(center, terms[0:1])
    self._test_terms(elab, terms[1:2])
    ps = head.children[10]
    self._test_edges(ps, [layer1.EdgeTags.Terminal,
                          layer1.EdgeTags.Terminal,
                          layer1.EdgeTags.Punctuation])
    self.assertTrue(ps.attrib.get("uncertain"))
    self.assertEqual(ps.children[0], terms[2])
    self.assertEqual(ps.children[1], terms[3])
    self.assertEqual(ps.children[2].children[0], terms[4])


def test_site_advanced(self):
    elem = load_xml("test_files/site3.xml")
    passage = convert.from_site(elem)
    terms = passage.layer(layer0.LAYER_ID).all
    l1 = passage.layer("1")

    # This passage has the same terminals as the simple and terminals test,
    # and have the same layer1 units for the first paragraph as the simple
    # test. In addition, it has the following annotation:
    # [6 7 8 9 H] [10 F] .
    # the 6-9 H has remote D which is [10 F]. Inside of 6-9, we have [8 S]
    # and [6 7 ... 9 A], where [6 E] and [7 ... 9 C].
    # [12 H] [13 H] [14 H] [15 L], where 15 linkage links 12, 13 and 14 and
    # [15 L] has an implicit Center unit
    head, lkg = l1.heads
    self._test_edges(head, [layer1.EdgeTags.Linker,
                            layer1.EdgeTags.ParallelScene,
                            layer1.EdgeTags.ParallelScene,
                            layer1.EdgeTags.Function,
                            layer1.EdgeTags.Punctuation,
                            layer1.EdgeTags.ParallelScene,
                            layer1.EdgeTags.ParallelScene,
                            layer1.EdgeTags.ParallelScene,
                            layer1.EdgeTags.Linker])

    # we only take what we haven"t checked already
    ps1, func, punct, ps2, ps3, ps4, link = head.children[2:]
    self._test_edges(ps1, [layer1.EdgeTags.Participant,
                           layer1.EdgeTags.Process,
                           layer1.EdgeTags.Adverbial])
    self.assertTrue(ps1[2].attrib.get("remote"))
    ps1_a, ps1_p, ps1_d = ps1.children
    self._test_edges(ps1_a, [layer1.EdgeTags.Elaborator,
                             layer1.EdgeTags.Center])
    self._test_terms(ps1_a.children[0], terms[5:6])
    self._test_terms(ps1_a.children[1], terms[6:9:2])
    self._test_terms(ps1_p, terms[7:8])
    self.assertEqual(ps1_d, func)
    self._test_terms(func, terms[9:10])
    self._test_terms(punct, terms[10:11])
    self._test_terms(ps2, terms[11:12])
    self._test_terms(ps3, terms[12:13])
    self._test_terms(ps4, terms[13:14])
    self.assertEqual(len(link), 2)
    self.assertEqual(link[0].tag, layer1.EdgeTags.Center)
    self.assertTrue(link.children[0].attrib.get("implicit"))
    self.assertEqual(link[1].tag, layer1.EdgeTags.Elaborator)
    self.assertEqual(link.children[1][0].tag, layer1.EdgeTags.Terminal)
    self.assertEqual(link.children[1][0].child, terms[14])
    self.assertEqual(lkg.relation, link)
    self.assertSequenceEqual(lkg.arguments, [ps2, ps3, ps4])


def test_to_standard(self):
    passage = convert.from_site(load_xml("test_files/site3.xml"))
    ref = load_xml("test_files/standard3.xml")
    root = convert.to_standard(passage)
    self.assertEqual(ETree.tostring(ref), ETree.tostring(root))


def test_from_standard(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    ref = convert.from_site(load_xml("test_files/site3.xml"))
    self.assertTrue(passage.equals(ref, ordered=True))


def test_from_text(self):
    sample = ["Hello . again", "nice", " ? ! end", ""]
    passage = next(convert.from_text(sample))
    terms = passage.layer(layer0.LAYER_ID).all
    pos = 0
    for i, par in enumerate(sample):
        for text in par.split():
            self.assertEqual(terms[pos].text, text)
            self.assertEqual(terms[pos].paragraph, i + 1)
            pos += 1


def test_from_text_long(self):
    sample = """
        After graduation, John moved to New York City.

        He liked it there. He played tennis.
        And basketball.

        And he lived happily ever after.
        """
    passages = list(convert.from_text(sample))
    self.assertEqual(len(passages), 3, list(map(convert.to_text, passages)))


def test_to_text(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    self.assertEqual(convert.to_text(passage, False)[0],
                     "1 2 3 4 . 6 7 8 9 10 . 12 13 14 15")
    self.assertSequenceEqual(convert.to_text(passage, True),
                             ["1 2 3 4 .", "6 7 8 9 10 .", "12 13 14 15"])


def test_to_site(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    root = convert.to_site(passage)
    copy = convert.from_site(root)
    self.assertTrue(passage.equals(copy))


def test_to_conll(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    converted = convert.to_conll(passage)
    with open("test_files/standard3.conll", encoding="utf-8") as f:
        # f.write("\n".join(converted))
        self.assertSequenceEqual(converted, f.read().splitlines() + [""])
    converted_passage = next(convert.from_conll(converted, passage.ID))
    # ioutil.passage2file(converted_passage, "test_files/standard3.conll.xml")
    ref = convert.from_standard(load_xml("test_files/standard3.conll.xml"))
    self.assertTrue(converted_passage.equals(ref))
    # Put the same sentence twice and try converting again
    for converted_passage in convert.from_conll(converted * 2, passage.ID):
        ref = convert.from_standard(load_xml("test_files/standard3.conll.xml"))
    self.assertTrue(converted_passage.equals(ref), "Passage does not match expected")


def test_to_sdp(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    converted = convert.to_sdp(passage)
    with open("test_files/standard3.sdp", encoding="utf-8") as f:
        # f.write("\n".join(converted))
        self.assertSequenceEqual(converted, f.read().splitlines() + [""])
    converted_passage = next(convert.from_sdp(converted, passage.ID))
    # ioutil.passage2file(converted_passage, "test_files/standard3.sdp.xml")
    ref = convert.from_standard(load_xml("test_files/standard3.sdp.xml"))
    self.assertTrue(converted_passage.equals(ref), "Passage does not match expected")


def test_to_export(self):
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    converted = convert.to_export(passage)
    with open("test_files/standard3.export", encoding="utf-8") as f:
        # f.write("\n".join(converted))
        self.assertSequenceEqual(converted, f.read().splitlines())
    converted_passage = next(convert.from_export(converted, passage.ID))
    # ioutil.passage2file(converted_passage, "test_files/standard3.export.xml")
    ref = convert.from_standard(load_xml("test_files/standard3.export.xml"))
    self.assertTrue(converted_passage.equals(ref), "Passage does not match expected")
