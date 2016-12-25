from argparse import ArgumentParser

from ucca.constructions import CONSTRUCTIONS, extract_units
from ucca.ioutil import read_files_and_dirs


if __name__ == "__main__":
    argparser = ArgumentParser(description="Extract linguistic constructions from UCCA corpus.")
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    for construction in CONSTRUCTIONS:
        argparser.add_argument("--%s" % construction.name.replace("_", "-"),
                               action="store_true", help="extract %s" % construction.description)
    args = argparser.parse_args()
    for passage in read_files_and_dirs(args.passages):
        extracted = extract_units(passage, args)
        if extracted:
            print("%s:" % passage.ID)
            for name, units in extracted.items():
                print("  %s:" % name)
                for unit in units:
                    print("    %s: %s" % (unit.ID, unit))
            print()
