from ucca import layer0, convert, textutil
from ucca.textutil import is_annotated
from .conftest import create_crossing_passage, create_multi_passage, create_passage, create_discontiguous, load_xml

"""Tests the textutil module functions and classes."""


def test_break2sentences():
    """Tests identifying correctly sentence ends.
    """
    p = create_multi_passage()
    assert textutil.break2sentences(p) == [4, 7, 11]


# def test_split_join_sentences_crossing():
#     """Test that splitting and joining a passage by sentences results in the same passage,
#     when the passage has edges crossing sentences.
#     """
#     p = create_crossing_passage()
#     split = textutil.split2sentences(p, remarks=True)
#     copy = textutil.join_passages(split)
#     diffutil.diff_passages(p, copy)
#     assert p.equals(copy))
#
# def test_split_join_paragraphs_crossing():
#     """Test that splitting and joining a passage by paragraphs results in the same passage
#     when the passage has edges crossing paragraphs.
#     """
#     p = create_crossing_passage()
#     split = textutil.split2paragraphs(p, remarks=True)
#     copy = textutil.join_passages(split)
#     diffutil.diff_passages(p, copy)
#     assert p.equals(copy))


def test_word_vectors():
    vectors, dim = textutil.get_word_vectors()
    for word, vector in vectors.items():
        assert len(vector) == dim, "Vector dimension for %s is %d != %d" % (word, len(vector), dim)


def test_annotate_passage():
    passage = convert.from_standard(load_xml("test_files/standard3.xml"))
    textutil.annotate(passage)
    textutil.annotate(passage, as_array=True)
    for p in passage, convert.from_standard(convert.to_standard(passage)):
        assert is_annotated(p, as_array=True), "Passage %s is not annotated" % passage.ID
        assert is_annotated(p, as_array=False), "Passage %s is not annotated" % passage.ID
        for terminal in p.layer(layer0.LAYER_ID).all:
            for attr in textutil.Attr:
                assert attr.key in terminal.extra, "Terminal %s has no %s" % (terminal, attr.name)
            assert terminal.tok is not None, "Terminal %s has no annotation" % terminal
            assert len(terminal.tok) == len(textutil.Attr)


def test_annotate_all():
    passages = [convert.from_standard(load_xml("test_files/standard3.xml")),
                create_passage(), create_crossing_passage(),
                create_discontiguous(), create_multi_passage()]
    list(textutil.annotate_all(passages))
    for passage, compare in textutil.annotate_all(((p, p) for p in passages), as_array=True, as_tuples=True):
        assert passage is compare
        for p in passage, convert.from_standard(convert.to_standard(passage)):
            assert is_annotated(p, as_array=True), "Passage %s is not annotated" % passage.ID
            assert is_annotated(p, as_array=False), "Passage %s is not annotated" % passage.ID
            for terminal in p.layer(layer0.LAYER_ID).all:
                for attr in textutil.Attr:
                    assert attr.key in terminal.extra, "Terminal %s in passage %s has no %s" % (
                        terminal, passage.ID, attr.name)
                assert terminal.tok is not None, "Terminal %s in passage %s has no annotation" % (terminal, passage.ID)
                assert len(terminal.tok) == len(textutil.Attr)
