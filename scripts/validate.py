import argparse

from ucca.ioutil import get_passages_with_progress_bar
from ucca.validation import validate


def main(args):
    for passage in get_passages_with_progress_bar(args.filenames, desc="Validating"):
        validate(passage)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Validate UCCA passages")
    argparser.add_argument("filenames", help="files or directories to validate")
    main(argparser.parse_args())
