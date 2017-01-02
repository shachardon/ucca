from argparse import ArgumentParser

from ucca import constructions
from ucca.ioutil import read_files_and_dirs
from ucca.tagutil import POS_TAGGERS


if __name__ == "__main__":
    argparser = ArgumentParser(description="Extract linguistic constructions from UCCA corpus.")
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    constructions.add_argument(argparser, False)
    argparser.add_argument("--pos-tagger", choices=POS_TAGGERS, default=POS_TAGGERS[0], help="POS tagger to use")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    args = argparser.parse_args()
    for passage in read_files_and_dirs(args.passages):
        print("%s:" % passage.ID)
        extracted = constructions.extract_edges(passage, args.constructions, args.pos_tagger, verbose=args.verbose)
        if extracted:
            for construction, edges in extracted.items():
                print("  %s:" % construction)
                for unit in edges:
                    print("    %s [%s %s]" % (unit, unit.tag, unit.child))
            print()
