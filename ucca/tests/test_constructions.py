import pytest

from ucca.constructions import extract_edges, CONSTRUCTION_BY_NAME, EDGE_TYPES_NAME
from .conftest import PASSAGES

"""Tests the constructions module functions and classes."""


@pytest.mark.parametrize("create", PASSAGES)
def test_evaluate_self(create):
    p = create()
    d = extract_edges(p)
    for construction in CONSTRUCTION_BY_NAME:
        if construction != EDGE_TYPES_NAME:
            assert construction in d
