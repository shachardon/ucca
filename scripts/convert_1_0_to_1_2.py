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


AUX = {"have", "be", "will", "to"}


def extract_aux(terminal):
    if get_annotation(terminal, Attr.LEMMA) in AUX:
        parent = fparent(terminal)
        grandparent = fparent(parent)
        if is_main_relation(grandparent) and (
                parent.ftag == layer1.EdgeTags.Function or
                parent.ftag in {layer1.EdgeTags.Elaborator, layer1.EdgeTags.Relator} and
                get_annotation(terminal, Attr.DEP) in {"aux", "auxpass"}):
            move_node(parent, grandparent, tag=layer1.EdgeTags.Function)
            return True
    return False


MODALS = {"can", "could", "may", "might", "shall", "should", "would", "must"}
SEMI_MODALS = {"ought", "have", "able", "want", "go"}


def extract_modal(terminal):
    lemma = get_annotation(terminal, Attr.LEMMA)
    if lemma in MODALS or lemma in SEMI_MODALS and get_annotation(terminal, Attr.DEP) not in {"aux", "auxpass"}:
        parent = fparent(terminal)
        grandparent = fparent(parent)
        if is_main_relation(grandparent) and parent.ftag == layer1.EdgeTags.Elaborator:
            move_node(parent, grandparent, tag=layer1.EdgeTags.Adverbial)
            return True
    return False


def extract_relator(terminal):
    parent = fparent(terminal)
    grandparent = fparent(parent)
    following_uncle = None
    for node in grandparent.iter():
        if node.start_position == 1 + terminal.position and \
                following_uncle.ftag in {layer1.EdgeTags.Participant, layer1.EdgeTags.Adverbial}:
            following_uncle = node
    if following_uncle is not None and is_main_relation(grandparent) and parent.ftag == layer1.EdgeTags.Relator and \
            grandparent.end_position == terminal.position:
        move_node(parent, following_uncle)
        return True
    return False


def flag_relator_starts_main_relation(terminal):
    parent = fparent(terminal)
    grandparent = fparent(parent)
    return grandparent.start_position == terminal.position and \
        is_main_relation(grandparent) and parent.ftag == layer1.EdgeTags.Relator


def flag_suspected_semi_modal(terminal):
    if get_annotation(terminal, Attr.DEP) not in {"det"}:
        parent = fparent(terminal)
        grandparent = fparent(parent)
        if is_main_relation(grandparent) and parent.ftag == layer1.EdgeTags.Elaborator:
            return True
    return False


RULES = (extract_aux, extract_modal, extract_relator, flag_relator_starts_main_relation, flag_suspected_semi_modal)


def convert_passage(passage, report_file):
    for rule in RULES:
        for terminal in passage.layer(layer0.LAYER_ID).all:
            if rule(terminal):
                print(rule.__name__, passage.ID, terminal.ID, terminal.text, file=report_file)


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
