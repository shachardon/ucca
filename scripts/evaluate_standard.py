#!/usr/bin/env python3
"""
The evaluation script for UCCA layer 1.
"""
from argparse import ArgumentParser

from ucca.evaluation import evaluate
from ucca.ioutil import file2passage
from ucca import constructions


if __name__ == "__main__":
    argparser = ArgumentParser(description="Compare two UCCA passages or two directories containing passage files.")
    argparser.add_argument("guessed", help="xml/pickle file name for the guessed annotation, or directory of files")
    argparser.add_argument("ref", help="xml/pickle file name for the reference annotation, or directory of files")
    argparser.add_argument("-u", "--units", action="store_true",
                           help="the units the annotations have in common, and those each has separately")
    argparser.add_argument("-f", "--fscore", action="store_true",
                           help="outputs the traditional P,R,F instead of the scene structure evaluation")
    argparser.add_argument("-e", "--errors", action="store_true",
                           help="prints the error distribution according to its frequency")
    constructions.add_argument(argparser)
    args = argparser.parse_args()

    if not (args.units or args.fscore or args.errors):
        argparser.error("At least one of -u, -f or -e is required.")

    guessed, ref = [file2passage(x) for x in (args.guessed, args.ref)]

    if args.units or args.fscore or args.errors:
        evaluate(guessed, ref, constructions=args.constructions,
                 units=args.units, fscore=args.fscore, errors=args.errors, verbose=True)
