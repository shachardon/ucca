import argparse
from posix import mkdir
from os import symlink, path, listdir

desc = """Split a directory of files into 'train', 'dev' and 'test' directories.
All files not in either 'train' or 'dev' will go into 'test'.
"""
TRAIN_DEFAULT = 290
DEV_DEFAULT = 35
# TEST on all the rest


def split_passages(directory, train=TRAIN_DEFAULT, dev=DEV_DEFAULT):
    for subdirectory in 'train', 'dev', 'test':
        if not path.exists(subdirectory):
            mkdir(subdirectory)
    filenames = sorted(listdir(directory))
    for f in filenames[:train]:
        symlink('../' + directory + f, 'train/' + f)
    for f in filenames[train:train + dev]:
        symlink('../' + directory + f, 'dev/' + f)
    for f in filenames[train + dev:]:
        symlink('../' + directory + f, 'test/' + f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('directory', default='.',
                        help="directory to split (default: current directory)")
    parser.add_argument('-t', '--train', default=TRAIN_DEFAULT,
                        help="size of train split (default: %d)" % TRAIN_DEFAULT)
    parser.add_argument('-d', '--dev', default=DEV_DEFAULT,
                        help="size of dev split (default: %d)" % DEV_DEFAULT)
    args = parser.parse_args()

    split_passages(args.directory, args.train, args.dev)
