from argparse import ArgumentParser

import matplotlib.pyplot as plt
from tqdm import tqdm

from ucca import visualization
from ucca.ioutil import get_passages_with_progress_bar

if __name__ == "__main__":
    argparser = ArgumentParser(description="Visualize the given passages as graphs.")
    argparser.add_argument("passages", nargs="+", help="UCCA passages, given as xml/pickle file names")
    argparser.add_argument("--tikz", action="store_true", help="print tikz code rather than showing plots")
    args = argparser.parse_args()
    for passage in get_passages_with_progress_bar(args.passages, desc="Visualizing"):
        if args.tikz:
            with tqdm.external_write_mode():
                print(visualization.tikz(passage))
        else:
            visualization.draw(passage)
            plt.show()
