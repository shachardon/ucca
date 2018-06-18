import pytest

from ucca import textutil
from ucca.constructions import extract_edges, CATEGORIES_NAME, DEFAULT, CONSTRUCTIONS
from .conftest import PASSAGES, loaded, loaded_valid, multi_sent, crossing, discontiguous, l1_passage, empty

"""Tests the constructions module functions and classes."""


def assert_spacy_not_loaded(*args, **kwargs):
    del args, kwargs
    assert False, "Should not load spaCy when passage is pre-annotated"


def extract_and_check(p, constructions=None, expected=None):
    d = extract_edges(p, constructions=constructions)
    if expected is not None:
        hist = {c.name: len(e) for c, e in d.items()}
        assert hist == expected, " != ".join(",".join(sorted(h)) for h in (hist, expected))


@pytest.mark.parametrize("create, expected", (
        (loaded, {'P': 1, 'remote': 1, 'E': 3, 'primary': 15, 'U': 2, 'F': 1, 'C': 3, 'Terminal': 15, 'LR': 1, 'A': 1,
                  'LA': 3, 'D': 1, 'L': 2, 'mwe': 2, 'H': 5}),
        (loaded_valid, {'P': 1, 'remote': 1, 'E': 3, 'primary': 15, 'U': 2, 'F': 1, 'C': 3, 'Terminal': 15, 'LR': 2,
                        'A': 1, 'LA': 5, 'D': 1, 'L': 2, 'mwe': 2, 'H': 5}),
        (multi_sent, {'U': 4, 'Terminal': 11, 'P': 3, 'mwe': 2, 'H': 3, 'primary': 6}),
        (crossing, {'U': 3, 'Terminal': 7, 'P': 2, 'remote': 1, 'mwe': 1, 'H': 2, 'primary': 3}),
        (discontiguous, {'G': 2, 'U': 2, 'remote': 1, 'E': 2, 'primary': 13, 'P': 3, 'F': 1, 'C': 1, 'Terminal': 20,
                         'A': 3, 'D': 2, 'mwe': 6, 'H': 3}),
        (l1_passage, {'P': 2, 'mwe': 4, 'H': 4, 'primary': 12, 'U': 2, 'Terminal': 20, 'LA': 3, 'A': 5, 'LR': 2, 'D': 1,
                      'L': 2, 'remote': 2, 'S': 1}),
        (empty, {}),
))
def test_extract_all(create, expected):
    extract_and_check(create(), constructions=CONSTRUCTIONS, expected=expected)


@pytest.mark.parametrize("create", PASSAGES)
@pytest.mark.parametrize("constructions", (DEFAULT, [CATEGORIES_NAME]), ids=("default", CATEGORIES_NAME))
def test_extract(create, constructions, monkeypatch):
    monkeypatch.setattr(textutil, "get_nlp", assert_spacy_not_loaded)
    extract_and_check(create(), constructions=constructions)
