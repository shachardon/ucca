"""
Oracle to produce gold transition parses given UCCA passages.
To be used for creating training and test data for a transition-based UCCA parser.
Implements the arc-eager algorithm.
"""


def get_action(passage, config):
    if config.stack and config.buffer:
        s = config.stack[-1]
        b = config.buffer[0]
        s_node = passage.by_id(s)
        b_node = passage.by_id(b)
        for edge in b_node.outgoing:
            if edge.child.ID == s:
                return "LEFT-ARC-" + edge.tag
        for edge in s_node.outgoing:
            if edge.child.ID == b:
                return "RIGHT-ARC-" + edge.tag
        for edge in b_node.outgoing + b_node.incoming:
            if edge.child.ID < s:
                return "REDUCE"
    return "SHIFT"
