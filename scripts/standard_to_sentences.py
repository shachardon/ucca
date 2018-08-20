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


class Splitter:
    def __init__(self, sentences, enum=False):
        self.sentences = sentences
        self.sentence_to_index = dict(map(reversed, enumerate(sentences)))
        self.enumerate = enum
        self.index = 0

    @classmethod
    def read_file(cls, filename, enum=False):
        if filename is None:
            return None
        with open(filename, encoding="utf-8") as f:
            sentences = [l.strip() for l in f]
        return cls(sentences, enum=enum)

    def split(self, passage):
        ends = []
        ids = []
        tokens = []
        for terminal in extract_terminals(passage):
            tokens.append(terminal.text)
            sentence = " ".join(tokens)
            # if len(tokens) > max(map(len, map(str.split, sentence_to_index))):
            #     raise ValueError("Failed matching '%s'" % sentence)
            if self.index is not None and self.index < len(self.sentences) and \
                    self.sentences[self.index].startswith(sentence):  # Try matching next sentence rather than shortest
                index = self.index if self.sentences[self.index] == sentence else None
            else:
                index = self.index = self.sentence_to_index.get(sentence)
            if index is not None:
                ends.append(terminal.position)
                ids.append(str(index))
                tokens = []
                self.index += 1
        return split_passage(passage, ends, ids=ids if self.enumerate else None)


def main(args):
    splitter = Splitter.read_file(args.sentences, enum=args.enumerate)
    os.makedirs(args.outdir, exist_ok=True)
    i = 0
    for passage in get_passages_with_progress_bar(args.filenames, "Splitting"):
        for sentence in splitter.split(passage) if splitter else split2sentences(
                passage, remarks=args.remarks, lang=args.lang, ids=map(str, count(i)) if args.enumerate else None):
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
