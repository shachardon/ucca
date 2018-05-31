import sys

import argparse

from ucca.ioutil import get_passages_with_progress_bar
from ucca.normalization import normalize
from ucca.validation import validate


def validate_passage(passage, normalization=False, extra=False):
    if normalization:
        normalize(passage, extra=extra)
    return list(validate(passage))


def main(args):
    errors = ((p.ID, validate_passage(p, args.normalize, args.extra))
              for p in get_passages_with_progress_bar(args.filenames, desc="Validating", converters={}))
    errors = {k: v for k, v in errors if v}
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
    argparser.add_argument("-n", "--normalize", action="store_true", help="normalize before validation")
    argparser.add_argument("-e", "--extra", action="store_true", help="extra normalization rules")
    main(check_args(argparser, argparser.parse_args()))
