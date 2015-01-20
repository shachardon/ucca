#!/usr/bin/python3


desc = """Trains MaltParser from NLTK on a given CoNLL file and parser another.
"""

import argparse
import sys
import nltk


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('train', help="CoNLL file name to train on")
    parser.add_argument('input', help="Text file to parse")
    parser.add_argument('output', help="File to write the parsed output to")
    args = parser.parse_args()

    parser = nltk.parse.malt.MaltParser(additional_java_args=['-Xmx512m'])
    parser.train_from_file(args.train)
    with open(args.input) as fin:
        output = parser.raw_parse(fin.read())
    with open(args.output, "w") as fout:
        fout.write(output)

    sys.exit(0)


if __name__ == '__main__':
    main()