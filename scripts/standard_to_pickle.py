#!/usr/bin/env python3
import argparse
import os
import sys

from ucca.ioutil import file2passage, passage2file

desc = """Parses an XML in UCCA standard format, and writes them in binary Pickle format."""


def main(args):
    for filename in args.filenames:
        print("Reading passage '%s'..." % filename, file=sys.stderr)
        passage = file2passage(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        outfile = args.outdir + os.path.sep + basename + ".pickle"
        print("Writing file '%s'..." % outfile, file=sys.stderr)
        passage2file(passage, outfile, binary=True)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('filenames', nargs='+', help="XML file names to convert")
    argparser.add_argument('-o', '--outdir', default='.', help="output directory")
    main(argparser.parse_args())
