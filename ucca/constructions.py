from collections import OrderedDict

from nltk.tag import map_tag

from ucca import tagutil, layer1
from ucca.layer1 import EdgeTags


class Construction(object):
    def __init__(self, name, description, criterion, default=False):
        """
        :param name: short name
        :param description: long description
        :param criterion: predicate function to apply to a Candidate, saying if it is an instance of this construction
        :param default: whether this construction is included in evaluation by default
        """
        self.name = name
        self.description = description
        self.criterion = criterion
        self.default = default

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


class Candidate(object):
    def __init__(self, edge):
        self.edge = edge
        try:
            self.terminals = edge.child.get_terminals()
        except AttributeError:
            self.terminals = ()
        self.coarse_tags = {map_tag("en-ptb", "universal", t.extra[tagutil.POS_TAG_KEY]) for t in self.terminals}
        self.tokens = {t.text.lower() for t in self.terminals}

    @property
    def remote(self):
        return self.edge.attrib.get("remote", False)

    @property
    def implicit(self):
        return self.edge.child.attrib.get("implicit", False)


EXCLUDED = (EdgeTags.Punctuation,
            EdgeTags.LinkArgument,
            EdgeTags.LinkRelation,
            EdgeTags.Terminal)
PRIMARY = "primary"
CONSTRUCTIONS = (
    Construction(PRIMARY, "Regular edges",
                 lambda c: not c.remote and not c.implicit and c.edge.tag not in EXCLUDED, default=True),
    Construction("remote", "Remote edges",
                 lambda c: c.remote and not c.implicit and c.edge.tag not in EXCLUDED, default=True),
    Construction("aspectual_verbs", "Aspectual verbs",
                 lambda c: c.coarse_tags == {"VERB"} and c.edge.tag == EdgeTags.Adverbial),
    Construction("light_verbs", "Light verbs",
                 lambda c: c.coarse_tags == {"VERB"} and c.edge.tag == EdgeTags.Function),
    # Construction("mwe", "Multi-word expressions"),
    Construction("pred_nouns", "Predicate nouns",
                 lambda c: c.coarse_tags == {"NOUN"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("pred_adjs", "Predicate adjectives",
                 lambda c: c.coarse_tags == {"ADJ"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("expletive_it", "Expletive `it' constructions",
                 lambda c: c.tokens == {"it"} and c.edge.tag == EdgeTags.Function),
    # Construction("part_whole", "Part-whole constructions"),
    # Construction("classifiers", "Classifier constructions"),
)
CONSTRUCTION_BY_NAME = OrderedDict((c.name, c) for c in CONSTRUCTIONS)
DEFAULT = OrderedDict((str(c), c) for c in CONSTRUCTIONS if c.default)


def add_argument(argparser, default=True):
    d = DEFAULT if default else [n for n in CONSTRUCTION_BY_NAME if n not in DEFAULT]
    argparser.add_argument("-c", "--constructions", nargs="+", choices=CONSTRUCTION_BY_NAME, default=d, metavar="x",
                           help="construction types to include, out of {%s} (default: %s)" %
                                (",".join(CONSTRUCTION_BY_NAME), ",".join(d)))


def extract_edges(passage, constructions=None, tagger=None, verbose=False):
    """
    Find constructions in UCCA passage.
    :param passage: Passage object to find constructions in
    :param constructions: list of constructions to include or None for all
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :return: dict of Construction -> list of corresponding edges
    """
    if constructions is None:
        constructions = CONSTRUCTIONS
    else:
        constructions = [c if isinstance(c, Construction) else CONSTRUCTION_BY_NAME[c] for c in constructions]
    tagutil.pos_tag(passage, tagger=tagger, verbose=verbose)
    extracted = OrderedDict((c, []) for c in constructions)
    for node in passage.layer(layer1.LAYER_ID).all:
        for edge in node:
            candidate = Candidate(edge)
            for construction in constructions:
                if construction.criterion(candidate):
                    extracted[construction].append(edge)
    # edges = (e for n in l1.all for e in n if e.tag)
    # for edge in edges:
    #     if args.mwe:
    #         pass
    #     if args.part_whole:
    #         pass
    #     if args.classifiers:
    #         pass
    return extracted
