#!/usr/bin/env python3
import sys

from ucca.convert import to_text

import argparse
import os
from tqdm import tqdm

from ucca.ioutil import file2passage, passage2file

desc = """Parses an XML in UCCA standard format, and writes their tokens into a text file."""


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    for filename in tqdm(args.filenames, desc="Converting", unit=" passages"):
        passage = file2passage(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        outfile = open(args.outdir + os.path.sep + basename + ".txt","w",encoding="utf-8")

        for line in to_text(passage, lang=args.lang):
            print(line, file=outfile)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('filenames', nargs='+', help="XML file names to convert")
    argparser.add_argument('-o', '--outdir', default='.', help="output directory")
    argparser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
    argparser.add_argument("-l", "--lang", default="en", help="language two-letter code for sentence model")

    main(argparser.parse_args())
