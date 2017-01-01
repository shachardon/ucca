from collections import defaultdict
from operator import attrgetter

from nltk.tag import map_tag

from ucca.layer1 import EdgeTags
from ucca import tagutil, layer0, layer1


class Construction(object):
    def __init__(self, name, description, coarse_tags=None, categories=None, tokens=None):
        self.name = name
        self.description = description
        self.coarse_tags = coarse_tags
        self.categories = categories
        self.tokens = tokens

    def __call__(self, coarse_tags, categories, tokens):
        return (self.coarse_tags is None or self.coarse_tags.issuperset(coarse_tags)) and \
               (self.categories is None or self.categories.issuperset(categories)) and \
               (self.tokens is None or self.tokens.issuperset(tokens))

    def __str__(self):
        return self.name


PREDICATE_EDGE_TAGS = {EdgeTags.Process, EdgeTags.State}


CONSTRUCTIONS = (
    Construction("aspectual_verbs", "aspectual verbs", {"VERB"}, {EdgeTags.Adverbial}),
    Construction("light_verbs", "light verbs", {"VERB"}, {EdgeTags.Function}),
    # Construction("mwe", "multi-word expressions"),
    Construction("pred_nouns", "predicate nouns", {"NOUN"}, PREDICATE_EDGE_TAGS),
    Construction("pred_adjs", "predicate adjectives", {"ADJ"}, PREDICATE_EDGE_TAGS),
    Construction("expletive_it", "expletive `it' constructions", categories={EdgeTags.Function}, tokens={"it"}),
    # Construction("part_whole", "part-whole constructions"),
    # Construction("classifiers", "classifier constructions"),
)


def extract_units(passage, args=None, tagger=None, verbose=False):
    """
    Find constructions in UCCA passage.
    :param passage: Passage object to find constructions in
    :param args: object with an attribute (with value True) for each desired construction, or None for all
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :return: dict of construction name -> list of corresponding units
    """
    tagutil.pos_tag(passage, tagger=tagger, verbose=verbose)
    units = defaultdict(list)
    nodes = list(passage.layer(layer0.LAYER_ID).all)
    visited = set()
    while nodes:  # bottom-up traversal
        node = nodes.pop(0)
        visited.add(node.ID)
        nodes += [n for n in node.parents if n.ID not in visited]
        try:
            terminals = node.get_terminals()
        except AttributeError:
            continue
        coarse_tags = [map_tag("en-ptb", "universal", t.extra[tagutil.POS_TAG_KEY]) for t in terminals]
        categories = [e.tag for e in node.incoming]
        tokens = [t.text.lower() for t in terminals]
        for construction in CONSTRUCTIONS:
            if (args is None or getattr(args, construction.name)) and construction(coarse_tags, categories, tokens):
                units[construction.name].append(node)
    # edges = (e for n in l1.all for e in n if e.tag)
    # for edge in edges:
    #     if args.mwe:
    #         pass
    #     if args.part_whole:
    #         pass
    #     if args.classifiers:
    #         pass
    return units
