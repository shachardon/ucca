from argparse import ArgumentParser

import matplotlib.pyplot as plt

from ucca import visualization
from ucca.ioutil import read_files_and_dirs

if __name__ == "__main__":
    argparser = ArgumentParser(description="Visualize the given passages as graphs.")
    argparser.add_argument("passages", nargs="+", help="UCCA passages, given as xml/pickle file names")
    argparser.add_argument("--tikz", action="store_true", help="print tikz code rather than showing plots")
    args = argparser.parse_args()
    for passage in read_files_and_dirs(args.passages):
        if args.tikz:
            print(visualization.tikz(passage))
        else:
            visualization.draw(passage)
            plt.show()
