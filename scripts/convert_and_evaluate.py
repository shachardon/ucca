#!/usr/bin/env python3

import argparse
import sys

from tqdm import tqdm

from ucca import convert
from ucca.evaluation import evaluate, Scores
from ucca.ioutil import get_passages_with_progress_bar

desc = """Parses files in CoNLL-X, SemEval 2015 SDP, NeGra export or text format,
converts to UCCA standard format, converts back to the original format and evaluates."""


def main(args):
    converter1 = convert.TO_FORMAT[args.format]
    converter2 = convert.FROM_FORMAT[args.format]
    scores = []
    for ref in get_passages_with_progress_bar(args.filenames, desc="Converting"):
        try:
            guessed = next(converter2(converter1(ref, tree=args.tree), ref.ID))
            scores.append(evaluate(guessed, ref, verbose=args.verbose))
        except Exception as e:
            if args.strict:
                raise ValueError("Error evaluating conversion of %s" % ref.ID) from e
            else:
                with tqdm.external_write_mode():
                    print("Error evaluating conversion of %s: %s" % (ref.ID, e), file=sys.stderr)
    print()
    if args.verbose and len(scores) > 1:
        print("Aggregated scores:")
    Scores.aggregate(scores).print()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="file names to convert and evaluate")
    argparser.add_argument("-f", "--format", required=True, choices=convert.CONVERTERS, help="input file format")
    argparser.add_argument("-T", "--tree", action="store_true", help="remove multiple parents to get a tree")
    argparser.add_argument("-s", "--strict", action="store_true",
                           help="stop immediately if failed to convert or evaluate a file")
    argparser.add_argument("-v", "--verbose", action="store_true",
                           help="print evaluation results for each file separately")
    main(argparser.parse_args())
