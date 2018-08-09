#!/usr/bin/env python3

import sys
from itertools import count

import argparse
import os

from ucca.convert import split2sentences, split_passage
from ucca.ioutil import passage2file, get_passages_with_progress_bar, external_write_mode
from ucca.normalization import normalize
from ucca.textutil import extract_terminals

desc = """Parses XML files in UCCA standard format, and writes a passage per sentence."""


def split(passage, order, enum=False):
    ends = []
    ids = []
    sentence = []
    for terminal in extract_terminals(passage):
        sentence.append(terminal.text)
        # if len(sentence) > max(map(len, map(str.split, order))):
        #     raise ValueError("Failed matching '%s'" % " ".join(sentence))
        index = order.get(" ".join(sentence))
        if index is not None:
            ends.append(terminal.position)
            ids.append(str(index))
            sentence = []
    return split_passage(passage, ends, ids=ids if enum else None)


def main(args):
    order = None
    if args.sentences:
        with open(args.sentences, encoding="utf-8") as f:
            order = dict(map(reversed, enumerate(map(str.strip, f))))
    os.makedirs(args.outdir, exist_ok=True)
    i = 0
    for passage in get_passages_with_progress_bar(args.filenames, "Splitting"):
        for sentence in split(passage, order, enum=args.enumerate) if order else split2sentences(
                passage, remarks=args.remarks, lang=args.lang, ids=count(i)):
            i += 1
            outfile = os.path.join(args.outdir, args.prefix + sentence.ID + (".pickle" if args.binary else ".xml"))
            with external_write_mode():
                print("Writing passage file for sentence '%s'..." % outfile, file=sys.stderr)
            if args.normalize:
                normalize(sentence)
            passage2file(sentence, outfile, binary=args.binary)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to convert")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
    argparser.add_argument("-r", "--remarks", action="store_true", help="annotate original IDs")
    argparser.add_argument("-l", "--lang", default="en", help="language two-letter code for sentence model")
    argparser.add_argument("-b", "--binary", action="store_true", help="write in pickle binary format (.pickle)")
    argparser.add_argument("-s", "--sentences", help="optional input file with sentence at each line to split by")
    argparser.add_argument("-e", "--enumerate", action="store_true", help="set each output sentence ID by global order")
    argparser.add_argument("-N", "--no-normalize", dest="normalize", action="store_false",
                           help="do not normalize passages after splitting")
    main(argparser.parse_args())
