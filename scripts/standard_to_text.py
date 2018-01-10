#!/usr/bin/env python3

import argparse
import re

from ucca.convert import to_text
from ucca.ioutil import read_files_and_dirs

desc = """Parses files in UCCA standard format, and writes a text file with a line per passage."""


def numeric(x):
    try:
        return tuple(map(int, re.findall("\d+", x)))
    except ValueError:
        return x


def main(args):
    with open(args.outfile, "w", encoding="utf-8") as f:
        for passage in read_files_and_dirs(sorted(args.filenames, key=numeric)):
            for line in to_text(passage):
                print(line, file=f)
    print("Wrote '%s'." % args.outfile)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to convert")
    argparser.add_argument("outfile", help="output file")
    main(argparser.parse_args())
