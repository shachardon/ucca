import argparse
from glob import glob
from posix import mkdir
from os import rename, symlink, path

desc = """Split a directory of files into 'train', 'dev' and 'test' directories.
All files not in either 'train' or 'dev' will go into 'test'.
"""
TRAIN_DEFAULT = 290
DEV_DEFAULT = 35
# TEST on all the rest

def split_passages(filenames, train=TRAIN_DEFAULT, dev=DEV_DEFAULT):
    for directory in 'train', 'dev', 'test':
        if not path.exists(directory):
            mkdir(directory)
    for f in filenames[:train]:
        symlink('../' + f, 'train/' + f)
    for f in filenames[train:train + dev]:
        symlink('../' + f, 'dev/' + f)
    for f in filenames[train + dev:]:
        symlink('../' + f, 'test/' + f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('filenames', default=glob('*'), nargs='*',
                        help="files to split (default: all in the current directory)")
    parser.add_argument('-t', '--train', default=TRAIN_DEFAULT,
                        help="size of train split (default: %d)" % TRAIN_DEFAULT)
    parser.add_argument('-d', '--dev', default=DEV_DEFAULT,
                        help="size of dev split (default: %d)" % DEV_DEFAULT)
    args = parser.parse_args()

    split_passages(sorted(args.filenames), args.train, args.dev)