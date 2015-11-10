from itertools import islice
from re import finditer

FEATURES = (
    # unigrams:
    "s0te", "s0we", "s1te", "s1we", "s2te", "s2we", "s3te", "s3we",
    "b0wt", "b1wt", "b2wt", "b3wt",
    "s0lwe", "s0rwe", "s0uwe", "s1lwe", "s1rwe", "s1uwe",
    # bigrams:
    "s0ws1w", "s0ws1e", "s0es1w", "s0es1e", "s0wb0w", "s0wb0t",
    "s0eb0w", "s0eb0t", "s1wb0w", "s1wb0t", "s1eb0w", "s1eb0t",
    "b0wb1w", "b02b1t", "b0tb1w", "b0tb1t",
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
)

FEATURE_TO_ATTRIBUTE = {"w": "text", "t": "pos_tag"}


def extract_features(state):
    """
    Calculate feature values according to current state
    :param state: current state of the parser
    """
    features = {}
    for feature in FEATURES:
        values = calc_feature(feature, state)
        if values is not None:
            features["%s=%s" % (feature, ",".join(values))] = 1
    return features


def calc_feature(feature, state):
    values = []
    for m in finditer("([sb])(\d+)([lru]*)([wtepq]+)", feature):
        source, index, children, properties = m.group(1, 2, 3, 4)
        index = int(index)
        if source == "s":
            if len(state.stack) <= index:
                return None
            node = state.stack[-1 - index]
        else:  # source == "b"
            if len(state.buffer) <= index:
                return None
            node = state.buffer[index]
        for child in children:
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
        for p in properties:
            v = get_prop(node, p)
            if v is None:
                return None
            values.append(v)
    return values


def get_prop(node, p):
    if p in "wt":
        return get_attr(node, FEATURE_TO_ATTRIBUTE[p])
    elif p == "e" and node.incoming:
        return node.incoming[0].tag
    else:
        return None
    # elif p == "p":  # TODO add these
    #     pass
    # elif p == "q":
    #     pass


def get_attr(node, attr):
    """
    If the node has only one terminal child (recursively) or is a terminal, return the
    terminal's attribute. Else, return None.
    :param node: a state Node object
    :param attr: the attribute name to get
    """
    while True:
        value = getattr(node, attr, None)
        if value is not None:
            return value
        if node.outgoing:
            node = node.outgoing[0].child
        else:
            return None
