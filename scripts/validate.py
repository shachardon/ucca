import sys

import argparse

from ucca.ioutil import get_passages_with_progress_bar
from ucca.validation import validate


def main(args):
    errors = ((p.ID, list(validate(p))) for p in get_passages_with_progress_bar(args.filenames, desc="Validating",
                                                                                converters={}))
    errors = {k: v for k, v in errors if v}
    if errors:
        id_len = max(map(len, errors))
        for passage_id, es in sorted(errors.items()):
            for i, e in enumerate(es):
                print("%-*s|%s" % (id_len, "" if i else passage_id, e))
        sys.exit(1)
    else:
        print("No errors found.")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Validate UCCA passages")
    argparser.add_argument("filenames", nargs="+", help="files or directories to validate")
    main(argparser.parse_args())
