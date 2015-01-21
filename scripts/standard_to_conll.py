#!/usr/bin/python3


desc = """Parses an XML in UCCA standard format, and writes as CoNLL-X format.
"""

import argparse
import sys
from xml.etree.ElementTree import ElementTree

import ucca.convert


def file2passage(filename):
    "Opens a file and returns its parsed Passage object"
    with open(filename) as f:
        etree = ElementTree().parse(f)
    return ucca.convert.from_standard(etree)


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', nargs='+', help="XML file names to convert")
    parser.add_argument('-o', '--outfile', help="output file for CoNLL")
    parser.add_argument('-t', '--test', type=bool, const=True, default=False, nargs='?',
                        help="omit head and deprel columns?")
    parser.add_argument('-s', '--sentences', type=bool, const=True, default=False, nargs='?',
                        help="split passages to sentences?")
    args = parser.parse_args()

    handle = open(args.outfile, 'w') if args.outfile else sys.stdout
    for filename in args.filenames:
        sys.stderr.write("Reading passage '%s'...\n" % filename)
        passage = file2passage(filename)
        output = ucca.convert.to_conll(passage, args.test, args.sentences)
        handle.write(output)
    if handle is not sys.stdout:
        handle.close()

    sys.exit(0)


if __name__ == '__main__':
    main()