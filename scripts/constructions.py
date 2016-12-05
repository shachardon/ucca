from argparse import ArgumentParser
from operator import attrgetter

from nltk.tag import pos_tag

from ucca.ioutil import read_files_and_dirs
from ucca.layer1 import EdgeTags


def is_verb(terminal):
    return terminal.pos_tag.startswith("VB")


def extract_units(args):
    units = []
    passages = read_files_and_dirs(args.passages)
    for passage in passages:
        l1 = passage.layer("1")
        terminals = sorted(l1.get_top_scene().get_terminals(), key=attrgetter("position"))
        tokens = map(attrgetter("text"), terminals)
        for (terminal, (token, tag)) in zip(terminals, pos_tag(tokens)):
            terminal.pos_tag = tag
            terminal.category = terminal.fparent.ftag
        if args.aspectual_verbs:
            units += [t for t in terminals if is_verb(t) and t.category == EdgeTags.Adverbial]
        if args.light_verbs:
            units += [t for t in terminals if is_verb(t) and t.category == EdgeTags.Function]
        if args.pred_nouns:
            pass
        if args.pred_adjs:
            pass
        if args.expletive_it:
            pass
        edges = (e for n in l1.all for e in n if e.tag)
        for edge in edges:
            if args.mwe:
                pass
            if args.part_whole:
                pass
            if args.classifiers:
                pass
    return units


if __name__ == "__main__":
    argparser = ArgumentParser(description="Extract linguistic constructions from UCCA corpus.")
    argparser.add_argument("passages", help="the corpus, given as xml/pickle file names")
    argparser.add_argument("--aspectual-verbs", action="store_true", help="extract aspectual verbs")
    argparser.add_argument("--light-verbs", action="store_true", help="extract light verbs")
    argparser.add_argument("--mwe", action="store_true", help="extract multi-word expressions")
    argparser.add_argument("--pred-nouns", action="store_true", help="extract predicate nouns")
    argparser.add_argument("--pred-adjs", action="store_true", help="extract predicate adjectives")
    argparser.add_argument("--expletive-it", action="store_true", help="extract expletive `it' constructions")
    argparser.add_argument("--part-whole", action="store_true", help="extract part-whole constructions")
    argparser.add_argument("--classifiers", action="store_true", help="extract classifier constructions")
    args = argparser.parse_args()

    units = extract_units(args)
    print(units)
