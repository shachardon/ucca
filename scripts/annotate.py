#!/usr/bin/env python3

import argparse
from glob import glob

from tqdm import tqdm

from ucca.ioutil import read_files_and_dirs, write_passage
from ucca.textutil import annotate_all, is_annotated

desc = """Read UCCA standard format in XML or binary pickle, and write back with POS tags and dependency parse."""


def main(args):
    for pattern in args.filenames:
        filenames = glob(pattern)
        if not filenames:
            raise IOError("Not found: " + pattern)
        passages = read_files_and_dirs(filenames)
        for passage in annotate_all(passages if args.verbose else
                                    tqdm(passages, unit=" passages", desc="Annotating " + pattern),
                                    replace=True, as_array=args.as_array, verbose=args.verbose):
            assert is_annotated(passage, args.as_array), "Passage %s is not annotated" % passage.ID
            write_passage(passage, outdir=args.out_dir, verbose=args.verbose)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to annotate")
    argparser.add_argument("-o", "--out-dir", default=".", help="directory to write annotated files to")
    argparser.add_argument("-a", "--as-array", action="store_true", help="save annotations as array in passage level")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
