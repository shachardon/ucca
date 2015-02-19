"""Utility functions for UCCA scripts."""

from xml.etree.ElementTree import ElementTree

from ucca.convert import from_standard


def file2passage(filename):
    "Opens a file and returns its parsed Passage object"
    with open(filename) as f:
        etree = ElementTree().parse(f)
    return from_standard(etree)