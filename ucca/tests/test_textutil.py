import pytest

from ucca import layer0, convert, textutil
from .conftest import crossing, multi_sent, l1_passage, discontiguous, empty, PASSAGES

"""Tests the textutil module functions and classes."""


@pytest.mark.parametrize("create, breaks", (
        (multi_sent, [4, 7, 11]),
        (crossing, [3, 7]),
        (discontiguous, [20]),
        (l1_passage, [20]),
        (empty, []),
))
def test_break2sentences(create, breaks):
    """Tests identifying correctly sentence ends. """
    assert textutil.break2sentences(create()) == breaks


def test_word_vectors():
    vectors, dim = textutil.get_word_vectors()
    for word, vector in vectors.items():
        assert len(vector) == dim, "Vector dimension for %s is %d != %d" % (word, len(vector), dim)


@pytest.mark.parametrize("create", PASSAGES)
@pytest.mark.parametrize("as_array", (True, False))
def test_annotate_passage(create, as_array):
    passage = create()
    textutil.annotate(passage, as_array=as_array)
    for p in passage, convert.from_standard(convert.to_standard(passage)):
        assert textutil.is_annotated(p, as_array=as_array), "Passage %s is not annotated" % passage.ID
        for terminal in p.layer(layer0.LAYER_ID).all:
            if as_array:
                assert terminal.tok is not None, "Terminal %s has no annotation" % terminal
                assert len(terminal.tok) == len(textutil.Attr)
            else:
                for attr in textutil.Attr:
                    assert attr.key in terminal.extra, "Terminal %s has no %s" % (terminal, attr.name)


@pytest.mark.parametrize("as_array", (True, False))
@pytest.mark.parametrize("convert_and_back", (True, False))
def test_annotate_all(as_array, convert_and_back):
    passages = [create() for create in PASSAGES]
    list(textutil.annotate_all(passages))
    for passage, compare in textutil.annotate_all(((p, p) for p in passages), as_array=as_array, as_tuples=True):
        assert passage is compare
        p = (passage, convert.from_standard(convert.to_standard(passage)))[convert_and_back]
        assert textutil.is_annotated(p, as_array=as_array), "Passage %s is not annotated" % passage.ID
        for terminal in p.layer(layer0.LAYER_ID).all:
            if as_array:
                assert terminal.tok is not None, "Terminal %s in passage %s has no annotation" % (terminal, passage.ID)
                assert len(terminal.tok) == len(textutil.Attr)
            else:
                for attr in textutil.Attr:
                    assert attr.key in terminal.extra, "Terminal %s in passage %s has no %s" % (
                        terminal, passage.ID, attr.name)
