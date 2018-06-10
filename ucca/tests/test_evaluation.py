import pytest

from ucca import core, layer0, layer1
from ucca.evaluation import evaluate, LABELED, UNLABELED
from .conftest import PASSAGES

"""Tests the evaluation module functions and classes."""


def passage1():
    p = core.Passage("1")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    # 20 terminals (1-20), #10 and #20 are punctuation
    terms = [l0.add_terminal(text=str(i), punct=(i % 10 == 0)) for i in range(1, 21)]

    # Linker #1 with terminal 1
    link1 = l1.add_fnode(None, layer1.EdgeTags.Linker)
    link1.add(layer1.EdgeTags.Terminal, terms[0])

    # Scene #1: [[2 3 4 5 P] [6 7 8 9 A] [10 U] H]
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    p1.add(layer1.EdgeTags.Terminal, terms[2])
    p1.add(layer1.EdgeTags.Terminal, terms[3])
    p1.add(layer1.EdgeTags.Terminal, terms[4])
    a1.add(layer1.EdgeTags.Terminal, terms[5])
    a1.add(layer1.EdgeTags.Terminal, terms[6])
    a1.add(layer1.EdgeTags.Terminal, terms[7])
    a1.add(layer1.EdgeTags.Terminal, terms[8])
    l1.add_punct(ps1, terms[9])

    # Scene #23: [[11 12 13 14 15 H] [16 L] [17 18 19 H] H]
    # Scene #2: [[11 12 13 14 P] [15 D]]
    ps23 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    ps2 = l1.add_fnode(ps23, layer1.EdgeTags.ParallelScene)
    a2 = l1.add_fnode(ps2, layer1.EdgeTags.Participant)
    a2.add(layer1.EdgeTags.Terminal, terms[10])
    a2.add(layer1.EdgeTags.Terminal, terms[11])
    a2.add(layer1.EdgeTags.Terminal, terms[12])
    a2.add(layer1.EdgeTags.Terminal, terms[13])
    d2 = l1.add_fnode(ps2, layer1.EdgeTags.Adverbial)
    d2.add(layer1.EdgeTags.Terminal, terms[14])

    # Linker #2: [16 L]
    link2 = l1.add_fnode(ps23, layer1.EdgeTags.Linker)
    link2.add(layer1.EdgeTags.Terminal, terms[15])

    # Scene #3: [[16 17 S] [18 A] (implicit participant) H]
    ps3 = l1.add_fnode(ps23, layer1.EdgeTags.ParallelScene)
    p3 = l1.add_fnode(ps3, layer1.EdgeTags.State)
    p3.add(layer1.EdgeTags.Terminal, terms[16])
    p3.add(layer1.EdgeTags.Terminal, terms[17])
    a3 = l1.add_fnode(ps3, layer1.EdgeTags.Participant)
    a3.add(layer1.EdgeTags.Terminal, terms[18])
    l1.add_fnode(ps3, layer1.EdgeTags.Participant, implicit=True)

    # Punctuation #20 - not under a scene
    l1.add_punct(None, terms[19])

    # adding remote argument to scene #1, remote process to scene #2
    # creating linkages L1->H1, H2<-L2->H3
    l1.add_remote(ps1, layer1.EdgeTags.Participant, d2)
    l1.add_remote(ps2, layer1.EdgeTags.Process, p1)
    l1.add_linkage(link1, ps1)
    l1.add_linkage(link2, ps2, ps3)

    return p


def passage2():
    p = core.Passage("2")
    l0 = layer0.Layer0(p)
    l1 = layer1.Layer1(p)
    # 20 terminals (1-20), #10 and #20 are punctuation
    terms = [l0.add_terminal(text=str(i), punct=(i % 10 == 0)) for i in range(1, 21)]

    # Linker #1 with terminal 1
    link1 = l1.add_fnode(None, layer1.EdgeTags.Linker)
    link1.add(layer1.EdgeTags.Terminal, terms[0])

    # Scene #1: [[2 3 4 5 P] [6 7 8 9 A] [10 U] H]
    ps1 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    p1 = l1.add_fnode(ps1, layer1.EdgeTags.Process)
    a1 = l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    p1.add(layer1.EdgeTags.Terminal, terms[1])
    p1.add(layer1.EdgeTags.Terminal, terms[2])
    p1.add(layer1.EdgeTags.Terminal, terms[3])
    p1.add(layer1.EdgeTags.Terminal, terms[4])
    a1.add(layer1.EdgeTags.Terminal, terms[5])
    a1.add(layer1.EdgeTags.Terminal, terms[6])
    a1.add(layer1.EdgeTags.Terminal, terms[7])
    a1.add(layer1.EdgeTags.Terminal, terms[8])
    l1.add_punct(ps1, terms[9])

    # Scene #23: [[11 12 13 14 15 H] [16 L] [17 18 19 H] H]
    # Scene #2: [[11 12 13 14 P] [15 D]]
    ps23 = l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    ps2 = l1.add_fnode(ps23, layer1.EdgeTags.ParallelScene)
    a2 = l1.add_fnode(ps2, layer1.EdgeTags.ParallelScene)
    a2.add(layer1.EdgeTags.Terminal, terms[10])
    a2.add(layer1.EdgeTags.Terminal, terms[11])
    a2.add(layer1.EdgeTags.Terminal, terms[12])
    a2.add(layer1.EdgeTags.Terminal, terms[13])
    d2 = l1.add_fnode(ps1, layer1.EdgeTags.Elaborator)
    d2.add(layer1.EdgeTags.Terminal, terms[14])

    # Linker #2: [16 L]
    link2 = l1.add_fnode(ps23, layer1.EdgeTags.Linker)
    link2.add(layer1.EdgeTags.Terminal, terms[15])

    # Scene #3: [[16 17 S] [18 A] (implicit participant) H]
    ps3 = l1.add_fnode(ps23, layer1.EdgeTags.ParallelScene)
    p3 = l1.add_fnode(ps3, layer1.EdgeTags.Process)
    p3.add(layer1.EdgeTags.Terminal, terms[16])
    p3.add(layer1.EdgeTags.Terminal, terms[17])
    a3 = l1.add_fnode(ps3, layer1.EdgeTags.Participant)
    a3.add(layer1.EdgeTags.Terminal, terms[18])
    l1.add_fnode(ps3, layer1.EdgeTags.Participant, implicit=True)

    # Punctuation #20 - not under a scene
    l1.add_punct(None, terms[19])

    # adding remote argument to scene #1, remote process to scene #2
    # creating linkages L1->H1, H2<-L2->H3
    l1.add_remote(ps1, layer1.EdgeTags.Participant, d2)
    l1.add_remote(ps1, layer1.EdgeTags.Participant, a3)
    l1.add_remote(ps2, layer1.EdgeTags.State, p1)
    l1.add_linkage(link1, ps1)
    l1.add_linkage(link2, ps2, ps3)

    return p


def check_primary_remote(scores, primary_labeled_f1, remote_labeled_f1, primary_unlabeled_f1, remote_unlabeled_f1):
    assert scores[LABELED]["primary"].f1 == primary_labeled_f1
    assert scores[LABELED]["remote"].f1 == remote_labeled_f1
    assert scores[UNLABELED]["primary"].f1 == primary_unlabeled_f1
    assert scores[UNLABELED]["remote"].f1 == remote_unlabeled_f1


@pytest.mark.parametrize("create", PASSAGES + (passage1, passage2))
@pytest.mark.parametrize("units", (True, False), ids=("units", ""))
@pytest.mark.parametrize("errors", (True, False), ids=("errors", ""))
@pytest.mark.parametrize("normalize", (True, False), ids=("normalize", ""))
def test_evaluate_self(create, units, errors, normalize):
    p = create()
    scores = evaluate(p, p, units=units, errors=errors, normalize=normalize)
    assert scores.average_f1() == 1.0
    for eval_type, results in scores.evaluators.items():
        for construction, stats in results.results.items():
            assert stats.f1 == 1.0, (eval_type, construction)
            assert stats.p == 1.0, (eval_type, construction)
            assert stats.r == 1.0, (eval_type, construction)
    check_primary_remote(scores, 1.0, 1.0, 1.0, 1.0)


@pytest.mark.parametrize("create1, create2, primary_labeled_f1, remote_labeled_f1,"
                         "primary_unlabeled_f1, remote_unlabeled_f1", (
                                 (passage1, passage2, 0.5, 0.4, 0.75, 0.8),
                         ))
@pytest.mark.parametrize("units", (True, False), ids=("units", ""))
@pytest.mark.parametrize("errors", (True, False), ids=("errors", ""))
def test_evaluate(create1, create2, primary_labeled_f1, remote_labeled_f1, primary_unlabeled_f1, remote_unlabeled_f1,
                  units, errors):
    scores = evaluate(create1(), create2(), units=units, errors=errors)
    check_primary_remote(scores, primary_labeled_f1, remote_labeled_f1, primary_unlabeled_f1, remote_unlabeled_f1)
