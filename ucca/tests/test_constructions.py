import pytest

from ucca import textutil
from ucca.constructions import extract_edges, CATEGORIES_NAME, DEFAULT
from .conftest import PASSAGES

"""Tests the constructions module functions and classes."""


def assert_spacy_not_loaded(*args, **kwargs):
    del args, kwargs
    assert False, "Should not load spaCy when passage is pre-annotated"


def extract_and_check(p, constructions=None, expected=None):
    d = extract_edges(p, constructions=constructions)
    if expected:
        for construction, size in expected.items():
            assert len(d[construction]) == size


@pytest.mark.parametrize("create", PASSAGES)
def test_extract_all(create):
    extract_and_check(create())


@pytest.mark.parametrize("create", PASSAGES)
@pytest.mark.parametrize("constructions", (DEFAULT, [CATEGORIES_NAME]))
def test_extract(create, constructions, monkeypatch):
    monkeypatch.setattr(textutil, "get_nlp", assert_spacy_not_loaded)
    extract_and_check(create(), constructions=constructions)
