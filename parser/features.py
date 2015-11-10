from itertools import islice


def extract_features(state):
    """
    Calculate feature values according to current state
    :param state: current state of the parser
    """
    features = {
        "#s": len(state.stack),
        "#b": len(state.buffer),
    }
    for i, node in enumerate(state.stack[-1:-4:-1]):
        add_features(features, node, "s%d" % i)
    for i, node in enumerate(islice(state.buffer, 0, 3)):
        add_features(features, node, "q%d" % i)
    return features


def add_features(features, node, name):
    text, tag = [get_attr(node, attr) for attr in ("text", "pos_tag")]
    if text is not None:
        features["%sw=%s" % (name, text)] = 1
    if tag is not None:
        features["%st=%s" % (name, tag)] = 1
    for edge in node.incoming:
        features["%sc=%s" % (name, edge.tag)] = 1


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
