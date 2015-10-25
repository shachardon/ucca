import argparse


class Config:
    def __init__(self):
        argparser = argparse.ArgumentParser(description="""Transition-based parser for UCCA.""")
        argparser.add_argument('train', nargs='+', help="passage file names to train on")
        argparser.add_argument('-t', '--test', nargs='+', help="passage file names to test on")
        argparser.add_argument('-o', '--outdir', default='.', help="output directory")
        argparser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
        argparser.add_argument('-v', '--verbose', action='store_true', default=False,
                               help="display detailed information while parsing")
        argparser.add_argument('-l', '--checkloops', action='store_true', default=False,
                               help="check for infinite loops")
        argparser.add_argument('-c', '--compoundswap', action='store_true', default=False,
                               help="enable compound swap")
        self.args = argparser.parse_args()
        Config.verbose = self.args.verbose
        Config.checkloops = self.args.checkloops
        Config.compoundswap = self.args.compoundswap
