"""Utility functions for UCCA scripts."""
import pickle

from xml.etree.ElementTree import ElementTree, tostring

from ucca.convert import from_standard, to_standard


def file2passage(filename):
    """Opens a file and returns its parsed Passage object
    Tries to read both as a standard XML file and as a binary pickle
    """
    try:
        with open(filename) as f:
            etree = ElementTree().parse(f)
        return from_standard(etree)
    except Exception as e:
        try:
            with open(filename, 'rb') as h:
                return pickle.load(h)
        except Exception:
            raise e


def passage2file(passage, filename, binary=False):
    """Writes a UCCA passage as a standard XML file or a binary pickle
    """
    if binary:
        with open(filename, 'wb') as h:
            pickle.dump(passage, h)
    else:  # xml
        root = to_standard(passage)
        output = indent_xml(tostring(root).decode())
        with open(filename, 'w') as h:
            h.write(output)


def indent_xml(xml_as_string):
    """Indents a string of XML-like objects.

    This works only for units with no text or tail members, and only for
    strings whose leaves are written as <tag /> and not <tag></tag>.

    """
    tabs = 0
    lines = str(xml_as_string).replace('><', '>\n<').splitlines()
    s = ''
    for line in lines:
        if line.startswith('</'):
            tabs -= 1
        s += ("  " * tabs) + line + '\n'
        if not (line.endswith('/>') or line.startswith('</')):
            tabs += 1
    return s