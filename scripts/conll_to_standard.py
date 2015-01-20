#!/usr/bin/python3


desc = """Parses a file in CoNLL-X format, and writes as XML in UCCA standard format.
"""

import argparse
import pickle
import sys

import ucca.convert
from site_to_standard import tostring, indent_xml


def file2passages(filename):
    "Opens a file and returns its parsed Passage objects"
    with open(filename) as f:
        for text in f.read().split("\n\n"):
            if text:
                yield ucca.convert.from_conll(text)


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filename', help="CoNLL file name to convert")
    parser.add_argument('-o', '--outdir', help="output directory for XML files")
    parser.add_argument('-b', '--binary', help="output file for binary pickel")
    args = parser.parse_args()

    passages = file2passages(args.filename)
    if args.binary:
        sys.stderr.write("Writing binary file '%s'...\n" % args.binary)
        with open(args.binary, 'wb') as handle:
            pickle.dump(passages, handle)
    else:
        for passage in passages:
            filename = "%s/%s.xml" % (args.outdir, passage.ID)
            sys.stderr.write("Writing passage '%s'...\n" % filename)
            root = ucca.convert.to_standard(passage)
            output = indent_xml(tostring(root).decode())
            with open(filename, 'w') as handle:
                handle.write(output)

    sys.exit(0)


if __name__ == '__main__':
    main()