import argparse
from posix import mkdir
from os import symlink, path, listdir
from shutil import copyfile

desc = """Split a directory of files into 'train', 'dev' and 'test' directories.
All files not in either 'train' or 'dev' will go into 'test'.
"""
TRAIN_DEFAULT = 290
DEV_DEFAULT = 35
# TEST on all the rest


def link(src, dest):
    try:
        symlink(src, dest)
    except NotImplementedError:
        copyfile(src, dest)

def split_passages(directory, train=TRAIN_DEFAULT, dev=DEV_DEFAULT):
    for subdirectory in 'train', 'dev', 'test':
        if not path.exists(subdirectory):
            mkdir(subdirectory)
    filenames = sorted(listdir(directory))
    print("Creating link in train/ to: ", end="")
    for f in filenames[:train]:
        symlink('../' + directory + f, 'train/' + f)
        print(f, end=" ")
    print()
    print("Creating link in dev/ to: ", end="")
    for f in filenames[train:train + dev]:
        symlink('../' + directory + f, 'dev/' + f)
        print(f, end=" ")
    print()
    print("Creating link in test/ to: ", end="")
    for f in filenames[train + dev:]:
        symlink('../' + directory + f, 'test/' + f)
        print(f, end=" ")
    print()

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
