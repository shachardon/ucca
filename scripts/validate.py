import argparse
from glob import glob

from tqdm import tqdm

from ucca.ioutil import read_files_and_dirs
from ucca.validation import validate


def main(args):
    for passage in tqdm(get_passages(args.filenames)):
        validate(passage)


def get_passages(patterns):
    for pattern in patterns:
        for filenames in glob(pattern) or [pattern]:
            for passage in read_files_and_dirs(filenames):
                yield passage


argparser = argparse.ArgumentParser(description="Validate UCCA passages")
argparser.add_argument("filenames", help="files or directories to validate")
main(argparser.parse_args())
