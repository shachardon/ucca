import pytest
from ucca import core, layer0, layer1
from ucca.normalization import normalize

"""Tests normalization module correctness and API."""


def root_scene():
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


def top_scene():
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


def nested_center():
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    terms = [l0.add_terminal(text=str(i), punct=False) for i in range(1, 4)]
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c1 = l1.add_fnode(a1, layer1.EdgeTags.Center)
    c2 = l1.add_fnode(c1, layer1.EdgeTags.Center)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c2.add(layer1.EdgeTags.Terminal, terms[0])
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    a2.add(layer1.EdgeTags.Terminal, terms[2])
    return p


def flat_center():
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    terms = [l0.add_terminal(text=str(i), punct=False) for i in range(1, 4)]
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c1 = l1.add_fnode(a1, layer1.EdgeTags.Center)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c1.add(layer1.EdgeTags.Terminal, terms[0])
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    a2.add(layer1.EdgeTags.Terminal, terms[2])
    return p


@pytest.mark.parametrize("unnormalized, normalized", (
        (root_scene, top_scene),
        (nested_center, flat_center),
))
def test_normalize(unnormalized, normalized):
    p1 = unnormalized()
    p2 = normalized()
    assert not p1.equals(p2), "Unnormalized and normalized passage"
    normalize(p1)
    assert str(p1) == str(p2), "Normalized passage string"
    assert p1.equals(p2), "Normalized passage"
