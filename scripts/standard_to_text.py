#!/usr/bin/env python3

import argparse
import re

from ucca.convert import to_text
from ucca.ioutil import get_passages_with_progress_bar

desc = """Parses files in UCCA standard format, and writes a text file with a line per passage."""


def numeric(x):
    try:
        return tuple(map(int, re.findall("\d+", x)))
    except ValueError:
        return x


def main(args):
    with open(args.outfile, "w", encoding="utf-8") as f:
        for passage in get_passages_with_progress_bar(sorted(args.filenames, key=numeric), desc="Converting to text"):
            for line in to_text(passage, lang=args.lang):
                print(line, file=f)
    print("Wrote '%s'." % args.outfile)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to convert")
    argparser.add_argument("outfile", help="output file")
    argparser.add_argument("-l", "--lang", default="en", help="language two-letter code for sentence model")
    main(argparser.parse_args())
