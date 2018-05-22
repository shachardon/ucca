import pytest

from ucca import core, layer0, layer1
from ucca.normalization import normalize

"""Tests normalization module correctness and API."""


def create_passage(num_terms=3, *punct):
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    terms = [l0.add_terminal(text=str(i), punct=(i in punct)) for i in range(1, num_terms + 1)]
    return p, l1, terms


def attach_terminals(terms, *nodes):
    for term, node in zip(terms, nodes):
        node.add(layer1.EdgeTags.Terminal, term)


def root_scene():
    p, l1, terms = create_passage()
    a1 = l1.add_fnode(None, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(None, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(None, layer1.EdgeTags.Participant)
    attach_terminals(terms, a1, p1, a2)
    return p


def top_scene():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, a1, p1, a2)
    return p


def nested_center():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c1 = l1.add_fnode(a1, layer1.EdgeTags.Center)
    c2 = l1.add_fnode(c1, layer1.EdgeTags.Center)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, c2, p1, a2)
    return p


def flat_center():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    c1 = l1.add_fnode(a1, layer1.EdgeTags.Center)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, c1, p1, a2)
    return p


def unary_punct():
    p, l1, terms = create_passage(3, 3)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, a1, p1)
    l1.add_punct(a2, terms[2])
    return p


def unattached_punct():
    p, l1, terms = create_passage(3, 3)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    return p


def top_punct():
    p, l1, terms = create_passage(3, 3)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    l1.add_punct(None, terms[2])
    return p


def attached_punct():
    p, l1, terms = create_passage(3, 3)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    l1.add_punct(ps1, terms[2])
    return p


def top_punct_only():
    p, l1, terms = create_passage(1, 1)
    l1.add_punct(None, terms[0])
    return p


def moved_punct():
    p, l1, terms = create_passage(3, 3)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    l1.add_punct(a1, terms[2])
    return p


def multi_punct():
    p, l1, terms = create_passage(4, 3, 4)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    punct1 = l1.add_punct(ps1, terms[2])
    punct1.add(layer1.EdgeTags.Terminal, terms[3])
    return p


def split_punct():
    p, l1, terms = create_passage(4, 3, 4)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    l1.add_punct(ps1, terms[2])
    l1.add_punct(ps1, terms[3])
    return p


def cycle():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    l1.add_remote(a2, layer1.EdgeTags.Elaborator, ps1)
    attach_terminals(terms, a1, p1, a2)
    return p


def unanalyzable():
    p, l1, terms = create_passage(5)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, a1, p1, a2, a2, a2)
    return p


def unanalyzable_punct():
    p, l1, terms = create_passage(5, 3, 4, 5)
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a2 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    attach_terminals(terms, a1, p1, a2, a2, a2)
    return p


def unattached_terms():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    attach_terminals(terms, a1, p1)
    return p


def attached_terms():
    p, l1, terms = create_passage()
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    f1 = l1.add_fnode(ps1, layer1.EdgeTags.Function)
    attach_terminals(terms, a1, p1, f1)
    return p


def normalize_and_compare(unnormalized, normalized, extra=False):
    p1 = unnormalized()
    p2 = normalized()
    if unnormalized != normalized:
        assert not p1.equals(p2), "Unnormalized and normalized passage: %s == %s" % (str(p1), str(p2))
    normalize(p1, extra=extra)
    assert p1.equals(p2), "Normalized passage: %s != %s" % (str(p1), str(p2))


@pytest.mark.parametrize("unnormalized, normalized", (
        (root_scene, top_scene),
        (nested_center, flat_center),
        (unary_punct, attached_punct),
        (unattached_punct, attached_punct),
        (top_punct, attached_punct),
        (top_punct_only, top_punct_only),
        (moved_punct, attached_punct),
        (multi_punct, split_punct),
        (cycle, top_scene),
        (unanalyzable, unanalyzable),
        (unanalyzable_punct, unanalyzable_punct),
))
def test_normalize(unnormalized, normalized):
    normalize_and_compare(unnormalized, normalized)


@pytest.mark.parametrize("unnormalized, normalized", (
        (unattached_terms, attached_terms),
))
def test_normalize_extra(unnormalized, normalized):
    normalize_and_compare(unnormalized, normalized, extra=True)
