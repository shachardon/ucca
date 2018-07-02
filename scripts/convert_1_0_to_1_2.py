import os
from argparse import ArgumentParser

from ucca import layer0, layer1
from ucca.ioutil import get_passages_with_progress_bar, write_passage
from ucca.normalization import fparent, remove, copy_edge
from ucca.textutil import annotate_all, Attr

desc = """Convert the English Wiki corpus from version 1.0 to 1.2"""


def get_annotation(terminal, attr):
    return terminal.extra[attr.key]


def is_main_relation(node):
    return node.ftag in {layer1.EdgeTags.Process, layer1.EdgeTags.State}


def move_node(node, new_parent, tag=None):
    for edge in node.incoming:
        copy_edge(edge, parent=fparent(new_parent), tag=tag)
        remove(edge.parent, edge)


def extract_aux(passage):
    for terminal in passage.layer(layer0.LAYER_ID).all:
        if get_annotation(terminal, Attr.LEMMA) in {"have", "be", "will", "to"}:
            parent = fparent(terminal)
            grandparent = fparent(parent)
            if is_main_relation(grandparent) and (
                    parent.ftag == layer1.EdgeTags.Function or
                    parent.ftag in {layer1.EdgeTags.Elaborator, layer1.EdgeTags.Relator} and
                    get_annotation(terminal, Attr.DEP) in {"aux", "auxpass"}):
                move_node(parent, grandparent, tag=layer1.EdgeTags.Function)
                yield terminal


def extract_modal(passage):
    for terminal in passage.layer(layer0.LAYER_ID).all:
        if get_annotation(terminal, Attr.LEMMA) in {"can"}:
            parent = fparent(terminal)
            grandparent = fparent(parent)
            if is_main_relation(grandparent) and parent.ftag == layer1.EdgeTags.Elaborator:
                move_node(parent, grandparent, tag=layer1.EdgeTags.Adverbial)
                yield terminal


RULES = (extract_aux, extract_modal)


def convert_passage(passage, report_file):
    for rule in RULES:
        for node in rule(passage):
            print(rule.__name__, passage.ID, node.ID, file=report_file)


def main(args):
    with open(args.outfile, "w", encoding="utf-8") as f:
        for passage in annotate_all(get_passages_with_progress_bar(args.passages), verbose=args.verbose):
            convert_passage(passage, report_file=f)
            write_passage(passage, outdir=args.outdir, verbose=args.verbose)
    print("Wrote '%s'" % args.outfile)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-O", "--outfile", default=os.path.splitext(argparser.prog)[0] + ".log", help="log file")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
