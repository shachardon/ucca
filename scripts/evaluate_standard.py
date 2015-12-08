#!/usr/bin/python3
"""
The evaluation software for UCCA layer 1.
"""
from argparse import ArgumentParser

from ucca.evaluation import evaluate
from ucca.ioutil import file2passage


#######################################################################################
# Returns the command line parser.
#######################################################################################
def cmd_line_parser():
    parser = ArgumentParser(description="Compare two UCCA passages.")
    parser.add_argument("guessed", help="xml/pickle file name for the guessed annotation")
    parser.add_argument("ref", help="xml/pickle file name for the reference annotation")
    parser.add_argument("--units", "-u", dest="units", action="store_true",
                        help="the units the annotations have in common, and those each has separately")
    parser.add_argument("--fscore", "-f", dest="fscore", action="store_true",
                        help="outputs the traditional P,R,F instead of the scene structure evaluation")
    parser.add_argument("--errors", "-e", dest="errors", action="store_true",
                        help="prints the error distribution according to its frequency")
    return parser


################
# MAIN         #
################

if __name__ == "__main__":
    argparser = cmd_line_parser()
    args = argparser.parse_args()

    if not (args.units or args.fscore or args.errors):
        argparser.error("At least one of -u, -f or -e is required.")

    guessed, ref = [file2passage(x) for x in (args.guessed, args.ref)]

    if args.units or args.fscore or args.errors:
        evaluate(guessed, ref,
                 units=args.units, fscore=args.fscore, errors=args.errors, verbose=True)
