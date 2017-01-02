from collections import defaultdict

from nltk.tag import map_tag

from ucca import tagutil, layer0
from ucca.layer1 import EdgeTags


class Construction(object):
    def __init__(self, name, description, criterion):
        """
        :param name: short name
        :param description: long description
        :param criterion: predicate function to apply to a Candidate, saying if it is an instance of this construction
        """
        self.name = name
        self.description = description
        self.criterion = criterion

    def __str__(self):
        return self.name


class Candidate(object):
    def __init__(self, edge):
        self.edge = edge
        try:
            self.terminals = edge.child.get_terminals()
        except AttributeError:
            self.terminals = ()
        self.coarse_tags = {map_tag("en-ptb", "universal", t.extra[tagutil.POS_TAG_KEY]) for t in self.terminals}
        self.tokens = {t.text.lower() for t in self.terminals}


CONSTRUCTIONS = (
    Construction("aspectual_verbs", "aspectual verbs",
                 lambda c: c.coarse_tags == {"VERB"} and c.edge.tag == EdgeTags.Adverbial),
    Construction("light_verbs", "light verbs",
                 lambda c: c.coarse_tags == {"VERB"} and c.edge.tag == EdgeTags.Function),
    # Construction("mwe", "multi-word expressions"),
    Construction("pred_nouns", "predicate nouns",
                 lambda c: c.coarse_tags == {"NOUN"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("pred_adjs", "predicate adjectives",
                 lambda c: c.coarse_tags == {"ADJ"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("expletive_it", "expletive `it' constructions",
                 lambda c: c.tokens == {"it"} and c.edge.tag == EdgeTags.Function),
    # Construction("part_whole", "part-whole constructions"),
    # Construction("classifiers", "classifier constructions"),
)


def extract_edges(passage, args=None, tagger=None, verbose=False):
    """
    Find constructions in UCCA passage.
    :param passage: Passage object to find constructions in
    :param args: object with an attribute (with value True) for each desired construction, or None for all
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :return: dict of construction name -> list of corresponding edges
    """
    tagutil.pos_tag(passage, tagger=tagger, verbose=verbose)
    extracted = defaultdict(list)
    edges = [e for n in passage.layer(layer0.LAYER_ID).all for e in n.incoming]
    visited_node_ids = set()
    while edges:  # bottom-up traversal
        edge = edges.pop(0)
        visited_node_ids.add(edge.parent.ID)
        edges += [e for e in edge.parent.incoming if e.parent.ID not in visited_node_ids]
        candidate = Candidate(edge)
        for construction in CONSTRUCTIONS:
            if (args is None or getattr(args, construction.name)) and construction.criterion(candidate):
                extracted[construction.name].append(edge)
    # edges = (e for n in l1.all for e in n if e.tag)
    # for edge in edges:
    #     if args.mwe:
    #         pass
    #     if args.part_whole:
    #         pass
    #     if args.classifiers:
    #         pass
    return extracted
