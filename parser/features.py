import re

from ucca import layer1

FEATURE_ELEMENT_PATTERN = re.compile("([sb])(\d)([lru]*)([wtepqPC]+)")
FEATURE_TEMPLATE_PATTERN = re.compile("^(%s)+$" % FEATURE_ELEMENT_PATTERN.pattern)

FEATURE_TEMPLATES = (
    # unigrams:
    "s0te", "s0we", "s1te", "s1we", "s2te", "s2we", "s3te", "s3we",
    "b0wt", "b1wt", "b2wt", "b3wt",
    "s0lwe", "s0rwe", "s0uwe", "s1lwe", "s1rwe", "s1uwe",
    # bigrams:
    "s0ws1w", "s0ws1e", "s0es1w", "s0es1e", "s0wb0w", "s0wb0t",
    "s0eb0w", "s0eb0t", "s1wb0w", "s1wb0t", "s1eb0w", "s1eb0t",
    "b0wb1w", "b0wb1t", "b0tb1w", "b0tb1t",
    # trigrams:
    "s0es1es2w", "s0es1es2e", "s0es1es2e", "s0es1eb0w", "s0es1eb0t",
    "s0es1wb0w", "s0es1wb0t", "s0ws1es2e", "s0ws1eb0t",
    # extended:
    "s0llwe", "s0lrwe", "s0luwe", "s0rlwe", "s0rrwe",
    "s0ruwe", "s0ulwe", "s0urwe", "s0uuwe", "s1llwe",
    "s1lrwe", "s1luwe", "s1rlwe", "s1rrwe", "s1ruwe",
    # separator:
    "s0wp", "s0wep", "s0wq", "s0weq", "s0es1ep", "s0es1eq",
    "s1wp", "s1wep", "s1wq", "s1weq",
    # counts:
    "s0P", "s0C", "s1P", "s0C",
)


class FeatureTemplate(object):
    """
    A feature template in parsed form, ready to be used for value calculation
    """
    def __init__(self, name, elements):
        """
        :param name: name of the feature in the short-hand form, to be used for the dictionary
        :param elements: collection of FeatureElement objects that represent the actual feature
        """
        self.name = name
        self.elements = elements


class FeatureTemplateElement(object):
    """
    One element in the values of a feature, e.g. from one node
    """
    def __init__(self, source, index, children, properties):
        """
        :param source: "s" or "b", whether the node comes from the stack or buffer respectively
        :param index: non-negative integer, the index of the element in the stack (reversed) or buffer
        :param children: possibly empty string in [lru]*, to select a (grand) child instead of the node
        :param properties: the actual values to choose, in [wtepq]+, if available (else omit feature)
                           w: node text
                           t: node POS tag
                           e: tag of first incoming edge
                           p: unique separator punctuation between nodes
                           q: count of any separator punctuation between nodes
                           P: number of parents
                           C: number of children
        """
        self.source = source
        self.index = int(index)
        self.children = children
        self.properties = properties


class FeatureExtractor(object):
    """
    Object to extract features from the parser state to be used in action classification
    """
    def __init__(self):
        assert all(FEATURE_TEMPLATE_PATTERN.match(f) for f in FEATURE_TEMPLATES),\
            "Features do not match pattern: " + ", ".join(f for f in FEATURE_TEMPLATES
                                                          if not FEATURE_TEMPLATE_PATTERN.match(f))
        # convert the list of features textual descriptions to the actual fields
        self.feature_templates = [FeatureTemplate(feature_name,
                                                  tuple(FeatureTemplateElement(*m.group(1, 2, 3, 4))
                                                        for m in re.finditer(FEATURE_ELEMENT_PATTERN,
                                                                             feature_name)))
                                  for feature_name in FEATURE_TEMPLATES]

    def extract_features(self, state):
        """
        Calculate feature values according to current state
        :param state: current state of the parser
        """
        features = {
            "b": 1,  # Bias
        }
        for feature_template in self.feature_templates:
            values = calc_feature(feature_template, state)
            if values is not None:
                features["%s=%s" % (feature_template.name, " ".join(values))] = 1
        return features


def calc_feature(feature_template, state):
    values = []
    for element in feature_template.elements:
        if element.source == "s":
            if len(state.stack) <= element.index:
                return None
            node = state.stack[-1 - element.index]
        else:  # source == "b"
            if len(state.buffer) <= element.index:
                return None
            node = state.buffer[element.index]
        for child in element.children:
            if not node.outgoing:
                return None
            if len(node.outgoing) == 1:
                if child == "u":
                    node = node.outgoing[0].child
            elif child == "l":
                node = node.outgoing[0].child
            elif child == "r":
                node = node.outgoing[-1].child
            else:  # child == "u" and len(node.outgoing) > 1
                return None
        for p in element.properties:
            v = get_prop(node, p)
            if v is None:
                return None
            values.append(str(v))
    return values


def get_prop(node, p):
    try:
        if p == "w":
            return get_head_terminal(node).text
        elif p == "t":
            return get_head_terminal(node).pos_tag
        elif p == "e" and node.incoming:
            return node.incoming[0].tag
        # elif p == "p":  # TODO add these
        #     pass
        # elif p == "q":
        #     pass
        elif p == "P":
            return len(node.incoming)
        elif p == "C":
            return len(node.outgoing)
    except AttributeError:
        pass
    return None


EDGE_PRIORITY = {tag: i for i, tag in enumerate((
    layer1.EdgeTags.Center,
    layer1.EdgeTags.Connector,
    layer1.EdgeTags.ParallelScene,
    layer1.EdgeTags.Process,
    layer1.EdgeTags.State,
    layer1.EdgeTags.Participant,
    layer1.EdgeTags.Adverbial,
    layer1.EdgeTags.Elaborator,
    layer1.EdgeTags.Relator,
    layer1.EdgeTags.Function,
    layer1.EdgeTags.Linker,
    layer1.EdgeTags.LinkRelation,
    layer1.EdgeTags.LinkArgument,
    layer1.EdgeTags.Ground,
    layer1.EdgeTags.Terminal,
    layer1.EdgeTags.Punctuation,
))}


def get_head_terminal(node):
    while node.text is None:  # Not a terminal
        if not node.outgoing:
            return None
        sorted_edges = sorted([edge for edge in node.outgoing
                               if not edge.remote and not edge.child.implicit],
                              key=lambda edge: EDGE_PRIORITY[edge.tag])
        node = sorted_edges[0].child
    return node
