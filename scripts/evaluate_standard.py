#!/usr/bin/env python3
"""
The evaluation script for UCCA layer 1.
"""
from argparse import ArgumentParser

import sys

from ucca import evaluation, constructions, ioutil


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
    argparser.add_argument("-v", "--verbose", action="store_true",
                           help="prints the results for every single pair (always true if there is only one pair)")
    constructions.add_argument(argparser)
    args = argparser.parse_args()

    if not (args.units or args.fscore or args.errors):
        argparser.error("At least one of -u, -f or -e is required.")

    guessed, ref = [ioutil.read_files_and_dirs((x,)) for x in (args.guessed, args.ref)]
    if len(guessed) != len(ref):
        raise ValueError("Number of passages to compare does not match: %d != %d" % (len(guessed), len(ref)))
    if len(guessed) > 1:
        guessed_by_id = {}
        for g in guessed:
            sys.stdout.write("\rReading %s..." % g.ID)
            sys.stdout.flush()
            guessed_by_id[g.ID] = g
        ids = [p.ID for p in ref]
        try:
            guessed = [guessed_by_id[i] for i in ids]
        except KeyError as e:
            raise ValueError("Passage IDs do not match") from e
    results = []
    for g, r in zip(guessed, ref):
        if len(guessed) > 1:
            sys.stdout.write("\rEvaluating %s:" % g.ID)
            sys.stdout.flush()
        if args.verbose:
            print()
        scores = evaluation.evaluate(g, r, constructions=args.constructions, units=args.units, fscore=args.fscore,
                                     errors=args.errors, verbose=args.verbose or len(guessed) == 1)
        if args.verbose:
            print("Average labeled F1 score: %.3f\n" % scores.average_f1())
        results.append(scores)
    scores = evaluation.Scores.aggregate(results)
    if len(results) > 1:
        if args.verbose:
            print("Aggregated scores:")
        scores.print()
        print("Average labeled F1 score: %.3f" % scores.average_f1())
