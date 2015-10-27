#!/usr/bin/python3
import os
import re
import argparse
import sys

import ucca.convert
from util import passage2file


desc = """Parses files in CoNLL-X format, and writes as XML in UCCA standard format, or as binary.
Each passage is written to the file:
<outdir>/<prefix><passage_id>.<extension>
"""


def conll2passage(filename, passage_id):
    """Opens a CONLL file and returns its parsed Passage objects"""
    with open(filename) as f:
        return ucca.convert.from_conll(f, passage_id)


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', nargs='+', help="CoNLL file names to convert")
    parser.add_argument('-o', '--outdir', default='.', help="output directory")
    parser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
    parser.add_argument('-b', '--binary', dest='binary', action='store_true',
                        help="write in pickle binary format (.bin)")
    parser.add_argument('-x', '--xml', dest='binary', action='store_false',
                        help="(default) write in standard XML format (.xml)")
    args = parser.parse_args()

    for filename in args.filenames:
        try:
            passage_id = re.search(r'\d+', os.path.basename(filename)).group(0)
        except AttributeError:
            sys.stderr.write("Error: cannot find passage ID in '%s'\n" % filename)
            continue
        passage = conll2passage(filename, passage_id)

        outfile = "%s/%s%s.%s" % (args.outdir, args.prefix, passage.ID,
                                  'pickle' if args.binary else 'xml')
        sys.stderr.write("Writing passage '%s'...\n" % outfile)
        passage2file(passage, outfile, args.binary)

    sys.exit(0)


if __name__ == '__main__':
    main()