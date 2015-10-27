import argparse


class Config:
    def __init__(self):
        argparser = argparse.ArgumentParser(description="""Transition-based parser for UCCA.""")
        argparser.add_argument('train', nargs='+', help="passage file names to train on")
        argparser.add_argument('-t', '--test', nargs='+', help="passage file names to test on")
        argparser.add_argument('-o', '--outdir', default='.', help="output directory")
        argparser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
        argparser.add_argument('-b', '--binary', action='store_true', default=False,
                               help="read and write passages in Pickle binary format, not XML")
        argparser.add_argument('-v', '--verbose', action='store_true', default=False,
                               help="display detailed information while parsing")
        argparser.add_argument('-l', '--checkloops', action='store_true', default=False,
                               help="check for infinite loops")
        argparser.add_argument('-V', '--verify', action='store_true', default=False,
                               help="verify oracle successfully reproduces the passage")
        argparser.add_argument('-c', '--compoundswap', action='store_true', default=False,
                               help="enable compound swap")
        argparser.add_argument('-s', '--seed', default=None, help="seed for np.random")
        self.args = argparser.parse_args()

        Config.verbose = self.args.verbose
        Config.line_end = "\n" if Config.verbose else " "  # show all in one line unless verbose

        Config.check_loops = self.args.checkloops
        Config.verify = self.args.verify

        Config.compound_swap = self.args.compoundswap
        Config.max_swap = 11
