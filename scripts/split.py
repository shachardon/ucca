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


def copy(src, dest, link=False):
    if link:
        try:
            symlink(src, dest)
        except (NotImplementedError, OSError):
            copyfile(src, dest)
    else:
        copyfile(src, dest)

def split_passages(directory, train=TRAIN_DEFAULT, dev=DEV_DEFAULT, link=False):
    for subdirectory in 'train', 'dev', 'test':
        if not path.exists(subdirectory):
            mkdir(subdirectory)
    filenames = sorted(listdir(directory))
    prefix = "../" if link else ""
    print_format = "Creating link in %s to: " if link else "Copying to %s: "
    if not directory.endswith("/"):
        directory = directory + "/"
    print(print_format % "train/", end="")
    for f in filenames[:train]:
        copy(prefix + directory + f, 'train/' + f, link)
        print(f, end=" ")
    print()
    print(print_format % "dev/", end="")
    for f in filenames[train:train + dev]:
        copy(prefix + directory + f, 'dev/' + f, link)
        print(f, end=" ")
    print()
    print(print_format % "test/", end="")
    for f in filenames[train + dev:]:
        copy(prefix + directory + f, 'test/' + f, link)
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
    parser.add_argument('-l', '--link', action='store_true',
                        help="create symbolic link instead of copying")
    args = parser.parse_args()

    split_passages(args.directory, args.train, args.dev, link=args.link)
