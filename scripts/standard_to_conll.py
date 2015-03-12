#!/usr/bin/python3

import argparse
import sys

import ucca.convert
from util import file2passage

desc = """Parses an XML in UCCA standard format, and writes as CoNLL-X format.
"""


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', nargs='+', help="passage file names to convert")
    parser.add_argument('-o', '--outdir', default='.', help="output directory")
    parser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
    parser.add_argument('-t', '--test', dest='test', action='store_true',
                        help="omit head and deprel columns")
    parser.add_argument('--no-test', dest='test', action='store_false',
                        help="(default) include head and deprel columns")
    parser.add_argument('-s', '--sentences', dest='sentences', action='store_true',
                        help="split passages to sentences")
    parser.add_argument('--no-sentences', dest='sentences', action='store_false',
                        help="(default) do not split passages to sentences")
    args = parser.parse_args()

    for filename in args.filenames:
        passage = file2passage(filename)
        output = ucca.convert.to_conll(passage, args.test, args.sentences)
        outfile = "%s/%s%s.conll" % (args.outdir, args.prefix, passage.ID)
        sys.stderr.write("Writing CONLL file '%s'...\n" % outfile)
        with open(outfile, 'w') as h:
            h.write(output)

    sys.exit(0)


if __name__ == '__main__':
    main()