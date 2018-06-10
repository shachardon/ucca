import pytest

from ucca.validation import validate
from .conftest import loaded, loaded_valid, multi_sent, crossing, discontiguous, l1_passage, empty

"""Tests the validation module functions and classes."""


@pytest.mark.parametrize("create, valid", (
        (loaded, False),
        (loaded_valid, True),
        (multi_sent, True),
        (crossing, True),
        (discontiguous, True),
        (l1_passage, True),
        (empty, True),
))
def test_evaluate_self(create, valid):
    p = create()
    errors = list(validate(p))
    if valid:
        assert not errors, p
    else:
        assert errors, p
