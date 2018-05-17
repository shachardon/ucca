import random

from ucca import layer0, layer1, convert, textutil, ioutil, diffutil
from ucca.convert import FROM_FORMAT
from ucca.textutil import is_annotated
from .conftest import create_crossing_passage, create_multi_passage, create_passage, create_discontiguous, load_xml

"""Tests the util module functions and classes."""


def test_break2sentences():
    """Tests identifying correctly sentence ends.
    """
    p = create_multi_passage()
    assert textutil.break2sentences(p) == [4, 7, 11]


def test_split2sentences():
    """Tests splitting a passage by sentence ends.
    """
    p = create_multi_passage()
    split = convert.split2sentences(p)
    assert len(split) == 3
    terms = [[t.text for t in s.layer(layer0.LAYER_ID).all] for s in split]
    assert terms[0] == ["1", "2", "3", "."]
    assert terms[1] == ["5", "6", "."]
    assert terms[2] == ["8", ".", "10", "."]
    assert all(t.paragraph == 1 for s in split for t in s.layer(layer0.LAYER_ID).all)
    top_scenes = [s.layer(layer1.LAYER_ID).top_scenes for s in split]
    for t in top_scenes:
        assert len(t) == 1
        assert t[0].incoming[0].tag == layer1.EdgeTags.ParallelScene


def test_split2paragraphs():
    """Tests splitting a passage by paragraph ends.
    """
    p = create_multi_passage()
    split = convert.split2paragraphs(p)
    assert len(split) == 2
    terms = [[t.text for t in s.layer(layer0.LAYER_ID).all] for s in split]
    assert terms[0] == ["1", "2", "3", ".", "5", "6", "."]
    assert terms[1] == ["8", ".", "10", "."]
    assert all(t.paragraph == 1 for s in split for t in s.layer(layer0.LAYER_ID).all)
    top_scenes = [s.layer(layer1.LAYER_ID).top_scenes for s in split]
    assert len(top_scenes[0]) == 2
    assert len(top_scenes[1]) == 1
    for t in top_scenes:
        for n in t:
            assert n.incoming[0].tag == layer1.EdgeTags.ParallelScene


def test_split_join_sentences():
    p = create_multi_passage()
    split = convert.split2sentences(p, remarks=True)
    copy = convert.join_passages(split)
    diffutil.diff_passages(p, copy)
    assert p.equals(copy)


def test_split_join_paragraphs():
    p = create_multi_passage()
    split = convert.split2paragraphs(p, remarks=True)
    copy = convert.join_passages(split)
    diffutil.diff_passages(p, copy)
    assert p.equals(copy)


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

def test_load_passages():
    """Test lazy-loading passages"""
    files = ["test_files/standard3.%s" % s for s in ("xml", "conll", "export", "sdp")]
    passages = ioutil.read_files_and_dirs(files, converters=FROM_FORMAT)
    assert len(files) == len(list(passages)), "Should load one passage per file"
    assert len(files) == len(passages)


def test_shuffle_passages():
    """Test lazy-loading passages and shuffling them"""
    files = ["test_files/standard3.%s" % s for s in ("xml", "conll", "export", "sdp")]
    passages = ioutil.read_files_and_dirs(files, converters=FROM_FORMAT)
    print("Passages:\n" + "\n".join(str(p.layer(layer1.LAYER_ID).heads[0]) for p in passages))
    random.shuffle(passages)
    print("Shuffled passages:\n" + "\n".join(str(p.layer(layer1.LAYER_ID).heads[0]) for p in passages))
    assert len(files) == len(passages)


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
