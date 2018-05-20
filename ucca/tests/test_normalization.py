from ucca import core, layer0, layer1
from ucca.normalization import normalize

"""Tests normalization module correctness and API."""


def normalized_passage():
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    terms = [l0.add_terminal(text=str(i), punct=False) for i in range(1, 4)]
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    a1.add(layer1.EdgeTags.Terminal, terms[0])
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    a2.add(layer1.EdgeTags.Terminal, terms[2])
    return p


def top_scene_passage():
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    terms = [l0.add_terminal(text=str(i), punct=False) for i in range(1, 4)]
    a1 = l1.add_fnode(None, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(None, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(None, layer1.EdgeTags.Participant)
    a1.add(layer1.EdgeTags.Terminal, terms[0])
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    a2.add(layer1.EdgeTags.Terminal, terms[2])
    return p


def test_normalize_top_scene():
    p1 = top_scene_passage()
    p2 = normalized_passage()
    assert not p1.equals(p2)
    normalize(p1)
    assert str(p1) == str(p2)
    assert p1.equals(p2)
