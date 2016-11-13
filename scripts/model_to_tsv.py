#!/usr/bin/python3

import argparse
import sys

import os
from linear.dense_perceptron import DensePerceptron
from linear.sparse_perceptron import SparsePerceptron

from parsing import config

desc = """Reads a model file in pickle format and writes as TSV
"""


def main():
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('model', choices=(config.SPARSE_PERCEPTRON, config.DENSE_PERCEPTRON), help="type of model")
    argparser.add_argument('infile', help="binary model file to read")
    argparser.add_argument('outfile', nargs="?", help="tsv file to write (if missing, <infile>.tsv)")
    args = argparser.parse_args()

    model = DensePerceptron() if args.model == config.DENSE_PERCEPTRON else SparsePerceptron()
    model.load(args.infile)
    model.write(args.outfile or os.path.splitext(args.infile)[0] + ".tsv")

    sys.exit(0)


if __name__ == '__main__':
    main()
