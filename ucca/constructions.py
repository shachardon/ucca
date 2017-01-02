from collections import defaultdict

from nltk.tag import map_tag

from ucca import tagutil, layer0
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


CONSTRUCTIONS = (
    Construction("primary", "Primary edges", True,
                 lambda c: not c.edge.attrib.get("remote", False)),
    Construction("remote", "Remote edges", True,
                 lambda c: c.edge.attrib.get("remote", False)),
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
NAMES = list(map(str, CONSTRUCTIONS))
DEFAULT = tuple([str(c) for c in CONSTRUCTIONS if c.default])


def add_argument(argparser, default=True):
    d = DEFAULT if default else [n for n in NAMES if n not in DEFAULT]
    argparser.add_argument("-c", "--constructions", nargs="+", choices=NAMES, default=d, metavar="x",
                           help="construction types to include, out of {%s} (default: %s)" %
                                (",".join(NAMES), ",".join(d)))


def extract_edges(passage, constructions=None, tagger=None, verbose=False):
    """
    Find constructions in UCCA passage.
    :param passage: Passage object to find constructions in
    :param constructions: list of constructions to include or None for all
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :return: dict of Construction -> list of corresponding edges
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
            if (constructions is None or construction.name in constructions) and construction.criterion(candidate):
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
