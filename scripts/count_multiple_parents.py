#!/usr/bin/python3
from collections import Counter

import argparse
import sys

desc = """Parses XML files in UCCA standard format, and creates a histogram for the number of parents per unit.
"""

from util import file2passage


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', nargs='+', help="XML file names to convert")
    parser.add_argument('-o', '--outfile', help="output file for histogram")
    args = parser.parse_args()

    histogram = Counter();
    for filename in args.filenames:
        sys.stderr.write("Reading passage '%s'...\n" % filename)
        passage = file2passage(filename)
        for node in passage.layer("1").all:
            histogram[len(node.incoming)] += 1

    handle = open(args.outfile, 'w') if args.outfile else sys.stdout
    handle.writelines(["%d,%d\n" % (parents, count) for parents, count in histogram.items()])
    if handle is not sys.stdout:
        handle.close()

    sys.exit(0)


if __name__ == '__main__':
    main()
