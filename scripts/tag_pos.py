#!/usr/bin/env python3

import argparse
import glob
import sys

from ucca.ioutil import file2passage, passage2file
from ucca.textutil import pos_tag

desc = """Read UCCA standard format in XML or binary pickle, and write back with POS tags."""


def main():
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to convert")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    args = argparser.parse_args()

    for pattern in args.filenames:
        filenames = glob.glob(pattern)
        if not filenames:
            raise IOError("Not found: " + pattern)
        for filename in filenames:
            passage = file2passage(filename)
            pos_tag(passage, verbose=args.verbose, replace=True)
            sys.stderr.write("Writing '%s'...\n" % filename)
            passage2file(passage, filename, binary=not filename.endswith("xml"))

    sys.exit(0)


if __name__ == '__main__':
    main()
