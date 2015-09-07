#!/usr/bin/python3

import argparse
import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

import layer0
import layer1

from util import file2passage

desc = """Prints statistics on UCCA passages
"""


def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-d', '--directory', help="directory containing XML files to process")
    parser.add_argument('-o', '--outfile', help="output file for data")
    parser.add_argument('-i', '--infile', help="input file for data")
    args = parser.parse_args()

    if args.directory:
        terminal_counts = []
        non_terminal_counts = []
        edge_counts = []
        for filename in glob.glob(args.directory + "/*.xml"):
            sys.stderr.write("Reading passage '%s'...\n" % filename)
            passage = file2passage(filename)
            terminal_counts.append(len(passage.layer(layer0.LAYER_ID).all))
            non_terminal_counts.append(len(passage.layer(layer1.LAYER_ID).all))
            edge_counts.append(len([edge for node in passage.nodes for edge in node]))
        data = np.array((terminal_counts, non_terminal_counts, edge_counts), dtype=int)
        if args.outfile:
            np.savetxt(args.outfile, data)
    elif args.infile:
        data = np.loadtxt(args.infile, dtype=int)
    else:
        raise Exception("Either --directory or --infile must be supplied")

    assert data, "Empty data"

    plt.scatter(data[0], data[1], label="nonterminals")
    plt.plot(data[0], 1.33 * data[0], label="y = 1.33 x")
    plt.xlabel("# terminals")
    plt.ylabel("# nonterminals")
    plt.legend()
    if args.outfile:
        plt.savefig(os.path.splitext(args.outfile)[0] + "_nonterms.png")

    plt.clf()
    plt.scatter(data[0], data[2], label="edges")
    plt.plot(data[0], 11.1 * data[0], label="y = 11.1 x")
    plt.xlabel("# terminals")
    plt.ylabel("# edges")
    plt.legend()
    if args.outfile:
        plt.savefig(os.path.splitext(args.outfile)[0] + "_edges.png")

    sys.exit(0)


if __name__ == '__main__':
    main()
