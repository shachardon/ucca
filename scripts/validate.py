import sys
from itertools import islice

import argparse
from multiprocessing import Pool

from ucca.ioutil import get_passages_with_progress_bar
from ucca.normalization import normalize
from ucca.validation import validate


class Validator:
    def __init__(self, normalization=False, extra=False, linkage=True):
        self.normalization = normalization
        self.extra = extra
        self.linkage = linkage

    def validate_passage(self, passage):
        if self.normalization:
            normalize(passage, extra=self.extra)
        return passage.ID, list(validate(passage, linkage=self.linkage))


def main(args):
    with Pool(10) as pool:
        errors = pool.map(Validator(args.normalize, args.extra, linkage=args.linkage).validate_passage,
                          get_passages_with_progress_bar(args.filenames, desc="Validating", converters={}))
    errors = dict(islice(((k, v) for k, v in errors if v), 1 if args.strict else None))
    if errors:
        id_len = max(map(len, errors))
        for passage_id, es in sorted(errors.items()):
            for i, e in enumerate(es):
                print("%-*s|%s" % (id_len, "" if i else passage_id, e))
        sys.exit(1)
    else:
        print("No errors found.")


def check_args(parser, args):
    if args.extra and not args.normalize:
        parser.error("Cannot specify --extra without --normalize")
    return args


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Validate UCCA passages")
    argparser.add_argument("filenames", nargs="+", help="files or directories to validate")
    argparser.add_argument("-S", "--strict", action="store_true", help="fail as soon as a violation is found")
    argparser.add_argument("-n", "--normalize", action="store_true", help="normalize before validation")
    argparser.add_argument("-e", "--extra", action="store_true", help="extra normalization rules")
    argparser.add_argument("--no-linkage", dest="linkage", action="store_false", help="skip linkage validations")
    main(check_args(argparser, argparser.parse_args()))
