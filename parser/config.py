VERBOSE = False  # print long trace of performed actions?
CHECK_LOOPS = False  # check whether an infinite loop is reached (adds runtime overhead)?
COMPOUND_SWAP = False  # whether to allow swap actions that move i steps rather than 1


def parse_args(argparser):
    global VERBOSE, CHECK_LOOPS, COMPOUND_SWAP
    argparser.add_argument('-v', '--verbose', action='store_true', default=VERBOSE,
                           help="display detailed information while parsing")
    argparser.add_argument('-l', '--checkloops', action='store_true', default=CHECK_LOOPS,
                           help="check for infinite loops")
    argparser.add_argument('-c', '--compoundswap', action='store_true', default=COMPOUND_SWAP,
                           help="enable compound swap")
    args = argparser.parse_args()
    VERBOSE = args.verbose
    CHECK_LOOPS = args.checkloops
    COMPOUND_SWAP = args.compoundswap
    return args
