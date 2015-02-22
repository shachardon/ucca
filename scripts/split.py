import argparse
from glob import glob
from posix import mkdir
from os import rename, path
from shutil import copyfile

desc = """Split a directory of files into 'train', 'dev' and 'test' directories.
Moves existing files into 'all' directory.
All files not in either 'train' or 'dev' will go into 'test'.
"""
TRAIN_DEFAULT = 300
DEV_DEFAULT = 30
# TEST on all the rest


def split_passages(filenames, train=TRAIN_DEFAULT, dev=DEV_DEFAULT):
    for directory in 'all', 'train', 'dev', 'test':
        if not path.exists(directory):
            mkdir(directory)
    for f in filenames:
        copyfile(f, 'all/' + f)
    for f in filenames[:train]:
        rename(f, 'train/' + f)
    for f in filenames[train:train + dev]:
        rename(f, 'dev/' + f)
    for f in filenames[train + dev:]:
        rename(f, 'test/' + f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', default=glob('*'), nargs='*',
                        help="files to split (default: all in the current directory)")
    parser.add_argument('-t', '--train', default=TRAIN_DEFAULT,
                        help="size of train split (default: %d)" % TRAIN_DEFAULT)
    parser.add_argument('-d', '--dev', default=DEV_DEFAULT,
                        help="size of dev split (default: %d)" % DEV_DEFAULT)
    args = parser.parse_args()

    split_passages(args.filenames, args.train, args.dev)