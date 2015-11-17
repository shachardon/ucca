import argparse


class Singleton(type):
    instance = None

    def __call__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


class Config(object, metaclass=Singleton):
    def __init__(self):
        argparser = argparse.ArgumentParser(description="""Transition-based parser for UCCA.""")
        argparser.add_argument('passages', nargs='*', help="passage files/directories to test on")
        argparser.add_argument('-m', '--model', default=None, help="model file to load/save")
        argparser.add_argument('-t', '--train', nargs='+', help="passage files/directories to train on")
        argparser.add_argument('-o', '--outdir', default='.', help="output directory")
        argparser.add_argument('-p', '--prefix', default='ucca_passage',
                               help="output filename prefix")
        argparser.add_argument('-I', '--iterations', type=int, default=1,
                               help="number of training iterations")
        argparser.add_argument('-b', '--binary', action='store_true', default=False,
                               help="read and write passages in Pickle binary format, not XML")
        argparser.add_argument('-v', '--verbose', action='store_true', default=False,
                               help="display detailed information while parsing")
        argparser.add_argument('-q', '--quiet', action='store_true', default=False,
                               help="display absolutely no information while parsing")
        argparser.add_argument('-l', '--checkloops', action='store_true', default=False,
                               help="check for infinite loops")
        argparser.add_argument('-V', '--verify', action='store_true', default=False,
                               help="verify oracle successfully reproduces the passage")
        argparser.add_argument('-c', '--compoundswap', action='store_true', default=False,
                               help="enable compound swap")
        argparser.add_argument('-S', '--maxswap', type=int, default=11,
                               help="maximum distance for compound swap")
        argparser.add_argument('-N', '--maxnodes', type=float, default=2.0,
                               help="maximum ratio between non-terminal to terminal nodes")
        argparser.add_argument('-P', '--overrideprob', type=float, default=1.0,
                               help="probability to override predicted action by true action during training")
        argparser.add_argument('-s', '--seed', type=int, default=None, help="seed for np.random")
        self.args = argparser.parse_args()

        self.iterations = self.args.iterations

        self.verbose = self.args.verbose
        self.line_end = "\n" if self.verbose else " "  # show all in one line unless verbose
        self.quiet = self.args.quiet
        assert not(self.verbose and self.quiet), "--verbose and --quiet are incompatible"

        self.check_loops = self.args.checkloops
        self.verify = self.args.verify

        self.compound_swap = self.args.compoundswap
        self.max_swap = self.args.maxswap

        self.max_nodes_ratio = self.args.maxnodes

        self.override_action_probability = self.args.overrideprob
        self.seed = self.args.seed
