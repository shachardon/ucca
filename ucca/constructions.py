from collections import OrderedDict

from ucca import textutil, layer0, layer1
from ucca.layer1 import EdgeTags, NodeTags


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
    def __init__(self, edge, reference=None):
        self.edge = edge
        self.reference = reference
        self._terminals = self._pos = self._dep = self._tokens = None

    def _init_terminals(self):
        if self._terminals is None:
            try:
                self._terminals = self.edge.child.get_terminals()
            except (AttributeError, ValueError):
                self._terminals = ()
            if self.reference is not None:
                self._terminals = [self.reference.by_id(t.ID) for t in self._terminals]

    @property
    def remote(self):
        return self.edge.attrib.get("remote", False)

    @property
    def implicit(self):
        return self.edge.child.attrib.get("implicit", False)

    @property
    def pos(self):
        if self._pos is None:
            self._init_terminals()
            self._pos = {t.extra[textutil.POS_KEY] for t in self._terminals}
        return self._pos

    @property
    def dep(self):
        if self._dep is None:
            self._init_terminals()
            self._dep = {t.extra[textutil.DEP_KEY] for t in self._terminals}
        return self._dep

    @property
    def tokens(self):
        if self._tokens is None:
            self._init_terminals()
            self._tokens = {t.text.lower() for t in self._terminals}
        return self._tokens


EXCLUDED = (EdgeTags.Punctuation,
            EdgeTags.LinkArgument,
            EdgeTags.LinkRelation,
            EdgeTags.Terminal)


def is_primary(c):
    return not c.remote and not c.implicit and c.edge.tag not in EXCLUDED


def is_remote(c):
    return c.remote and not c.implicit and c.edge.tag not in EXCLUDED


CONSTRUCTIONS = (
    Construction("primary", "Regular edges", is_primary, default=True),
    Construction("remote", "Remote edges", is_remote, default=True),
    Construction("aspectual_verbs", "Aspectual verbs",
                 lambda c: c.pos == {"VERB"} and c.edge.tag == EdgeTags.Adverbial),
    Construction("light_verbs", "Light verbs",
                 lambda c: c.pos == {"VERB"} and c.edge.tag == EdgeTags.Function),
    Construction("mwe", "Multi-word expressions",
                 lambda c: is_primary(c) and c.edge.child.tag == NodeTags.Foundational and len(
                     c.edge.child.terminals) > 1),  # inseparable unit
    Construction("pred_nouns", "Predicate nouns",
                 lambda c: c.pos == {"NOUN"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("pred_adjs", "Predicate adjectives",
                 lambda c: c.pos == {"ADJ"} and c.edge.tag in {EdgeTags.Process, EdgeTags.State}),
    Construction("expletives", "Expletives",
                 lambda c: c.tokens <= {"it", "there"} and c.edge.tag == EdgeTags.Function),
    # Construction("part_whole", "Part-whole constructions"),
    # Construction("classifiers", "Classifier constructions"),
)
PRIMARY = CONSTRUCTIONS[0]
CONSTRUCTION_BY_NAME = OrderedDict((c.name, c) for c in CONSTRUCTIONS)
DEFAULT = OrderedDict((str(c), c) for c in CONSTRUCTIONS if c.default)


def add_argument(argparser, default=True):
    d = list(DEFAULT.keys()) if default else [n for n in CONSTRUCTION_BY_NAME if n not in DEFAULT]
    argparser.add_argument("--constructions", nargs="*", choices=CONSTRUCTION_BY_NAME, default=d, metavar="x",
                           help="construction types to include, out of {%s}" %
                                ",".join(CONSTRUCTION_BY_NAME.keys()))


def get_by_names(constructions):
    return [c if isinstance(c, Construction) else CONSTRUCTION_BY_NAME[c] for c in constructions] \
        if constructions else CONSTRUCTIONS


def terminal_ids(passage):
    return {t.ID for t in passage.layer(layer0.LAYER_ID).all}


def extract_edges(passage, constructions=None, reference=None, verbose=False):
    """
    Find constructions in UCCA passage.
    :param passage: Passage object to find constructions in
    :param constructions: list of constructions to include or None for all
    :param reference: Passage object to get POS tags from (default: `passage')
    :param verbose: whether to print tagged text
    :return: dict of Construction -> list of corresponding edges
    """
    constructions = get_by_names(constructions)
    if reference is not None:
        assert terminal_ids(passage) == terminal_ids(reference),\
            "Reference passage terminals do not match: %s" % reference.ID
    textutil.annotate(passage, verbose=verbose)
    extracted = OrderedDict((c, []) for c in constructions)
    for node in passage.layer(layer1.LAYER_ID).all:
        for edge in node:
            candidate = Candidate(edge, reference=reference)
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
