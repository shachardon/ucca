import os
import pytest
import random
from glob import glob

from ucca import layer0, layer1, convert, ioutil, diffutil
from ucca.convert import FROM_FORMAT
from .conftest import loaded, multi_sent, discontiguous, l1_passage

"""Tests the ioutil module functions and classes."""


def test_split2sentences():
    """Tests splitting a passage by sentence ends.
    """
    p = multi_sent()
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
    p = multi_sent()
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


@pytest.mark.parametrize("create", (loaded, multi_sent, discontiguous, l1_passage))
def test_split_join_sentences(create):
    p = create()
    split = convert.split2sentences(p, remarks=True)
    copy = convert.join_passages(split)
    diffutil.diff_passages(p, copy)
    assert p.equals(copy)


@pytest.mark.parametrize("create", (loaded, multi_sent, discontiguous, l1_passage))
def test_split_join_paragraphs(create):
    p = create()
    split = convert.split2paragraphs(p, remarks=True)
    copy = convert.join_passages(split)
    diffutil.diff_passages(p, copy)
    assert p.equals(copy)


FORMATS = ("xml", "conll", "export", "sdp")


def _test_passages(passages):
    for passage in passages:
        assert passage.layer(layer0.LAYER_ID).all, "No terminals in passage " + passage.ID
        assert len(passage.layer(layer1.LAYER_ID).all), "No non-terminals but the root in passage " + passage.ID


@pytest.mark.parametrize("suffix", FORMATS)
def test_load_passage(suffix):
    _test_passages(ioutil.read_files_and_dirs(glob(os.path.join("test_files", "standard3." + suffix)),
                                              converters=FROM_FORMAT))


def test_load_multiple_passages():
    """Test lazy-loading passages"""
    files = ["test_files/standard3.%s" % s for s in FORMATS]
    passages = ioutil.read_files_and_dirs(files, converters=FROM_FORMAT)
    assert len(files) == len(list(passages)), "Should load one passage per file"
    assert len(files) == len(passages)
    _test_passages(passages)


def test_shuffle_passages():
    """Test lazy-loading passages and shuffling them"""
    files = ["test_files/standard3.%s" % s for s in FORMATS]
    passages = ioutil.read_files_and_dirs(files, converters=FROM_FORMAT)
    print("Passages:\n" + "\n".join(str(p.layer(layer1.LAYER_ID).heads[0]) for p in passages))
    random.shuffle(passages)
    print("Shuffled passages:\n" + "\n".join(str(p.layer(layer1.LAYER_ID).heads[0]) for p in passages))
    assert len(files) == len(passages)
    _test_passages(passages)
