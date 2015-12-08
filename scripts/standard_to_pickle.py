#!/usr/bin/python3
import os
import argparse
import sys

from textutil import file2passage, passage2file


desc = """Parses an XML in UCCA standard format, and writes them in binary Pickle format.
"""


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', nargs='+', help="XML file names to convert")
    parser.add_argument('-o', '--outdir', default='.', help="output directory")
    args = parser.parse_args()

    for filename in args.filenames:
        sys.stderr.write("Reading passage '%s'...\n" % filename)
        passage = file2passage(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        outfile = args.outdir + os.path.sep + basename + ".pickle"
        sys.stderr.write("Writing file '%s'...\n" % outfile)
        passage2file(passage, outfile, binary=True)

    sys.exit(0)


if __name__ == '__main__':
    main()
