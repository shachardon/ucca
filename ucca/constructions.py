from collections import defaultdict
from operator import attrgetter

from nltk.tag import map_tag

from ucca.layer1 import EdgeTags
from ucca import tagutil, layer1


class Construction(object):
    def __init__(self, name, description, coarse_tags=None, categories=None, tokens=None):
        self.name = name
        self.description = description
        self.coarse_tags = coarse_tags
        self.categories = categories
        self.tokens = tokens

    def __call__(self, coarse_tag, category, token):
        return (self.coarse_tags is None or coarse_tag in self.coarse_tags) and \
               (self.categories is None or category in self.categories) and \
               (self.tokens is None or token in self.tokens)

    def __str__(self):
        return self.name


PREDICATES = (EdgeTags.Process, EdgeTags.State)


CONSTRUCTIONS = (
    Construction("aspectual_verbs", "aspectual verbs", ("VERB",), (EdgeTags.Adverbial,)),
    Construction("light_verbs", "light verbs", ("VERB",), (EdgeTags.Function,)),
    # Construction("mwe", "multi-word expressions"),
    Construction("pred_nouns", "predicate nouns", ("NOUN",), PREDICATES),
    Construction("pred_adjs", "predicate adjectives", ("ADJ",), PREDICATES),
    Construction("expletive_it", "expletive `it' constructions", categories=(EdgeTags.Function,), tokens="it"),
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
    units = defaultdict(list)
    l1 = passage.layer(layer1.LAYER_ID)
    for terminal in sorted(l1.heads[0].get_terminals(), key=attrgetter("position")):
        tag = terminal.extra.get(tagutil.POS_TAG_KEY)
        if tag is None:
            tagutil.pos_tag(passage, tagger=tagger, verbose=verbose)
            try:
                tag = terminal.extra[tagutil.POS_TAG_KEY]
            except KeyError as e:
                raise Exception("Failed getting POS tag for '%s'" % terminal) from e
        coarse_tag = map_tag("en-ptb", "universal", tag)
        p = terminal
        while not hasattr(p, "ftag"):
            p = p.parents[0]
        category = p.ftag
        for construction in CONSTRUCTIONS:
            if (args is None or getattr(args, construction.name)) and \
                    construction(coarse_tag, category, terminal.text.lower()):
                units[construction.name].append(terminal)
    # edges = (e for n in l1.all for e in n if e.tag)
    # for edge in edges:
    #     if args.mwe:
    #         pass
    #     if args.part_whole:
    #         pass
    #     if args.classifiers:
    #         pass
    return units
