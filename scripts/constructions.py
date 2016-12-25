from argparse import ArgumentParser
from operator import attrgetter

from nltk.tag import pos_tag, map_tag

from ucca.ioutil import read_files_and_dirs
from ucca.layer1 import EdgeTags


PREDICATES = (EdgeTags.Process, EdgeTags.State)


def extract_units(args):
    units = []
    passages = read_files_and_dirs(args.passages)
    for passage in passages:
        l1 = passage.layer("1")
        terminals = sorted(l1.heads[0].get_terminals(), key=attrgetter("position"))
        for (terminal, (token, tag)) in zip(terminals, pos_tag([t.text for t in terminals])):
            coarse_tag = map_tag('en-ptb', 'universal', tag)
            p = terminal
            while not hasattr(p, "ftag"):
                p = p.parents[0]
            category = p.ftag
            if coarse_tag == "VERB" and (
                    args.aspectual_verbs and category == EdgeTags.Adverbial or
                    args.light_verbs and category == EdgeTags.Function) or \
                category in PREDICATES and (
                    args.pred_nouns and coarse_tag == "NOUN" or
                    args.pred_adjs and coarse_tag == "ADJ") or \
                args.expletive_it and category == EdgeTags.Function and token.lower() == "it":
                units.append(terminal)
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
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
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
    print("\n".join(map(str, units)))
