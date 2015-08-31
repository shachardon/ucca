"""
Oracle to produce gold transition parses given UCCA passages.
To be used for creating training and test data for a transition-based UCCA parser.
Implements the arc-eager algorithm.
"""


class Oracle:
    def __init__(self, passage):
        self.edges_done = set()
        self.passage = passage

    def filter_edges_done(self, edges):
        return [e for e in edges if e not in self.edges_done]

    def get_action(self, config):
        if config.stack and config.buffer:
            s = self.passage.by_id(config.stack[-1].node_id)
            b = self.passage.by_id(config.buffer[0].node_id)
            for edge in self.filter_edges_done(s.incoming):
                if len(edge.parent.outgoing) == 1:
                    self.edges_done.add(edge)
                    return "UNARY-" + edge.tag, edge.parent.ID
            for edge in self.filter_edges_done(b.outgoing):  # FIXME not possible since only terminals are on buffer
                if edge.child.ID == s.ID:
                    self.edges_done.add(edge)
                    return "LEFT-ARC-" + edge.tag, edge.parent.ID
            for edge in self.filter_edges_done(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_done.add(edge)
                    return "RIGHT-ARC-" + edge.tag, edge.parent.ID
            if not self.filter_edges_done(s.outgoing + s.incoming):
                return "REDUCE", None
        return "SHIFT", None

"""
def get_action(passage, config):
    if config.stack and config.buffer:
        s = config.stack[-1]
        b = config.buffer[0]
        if len(s.incoming) == 1:
            return "UNARY-" + s.incoming.itervalues().next()
        for child_index, edge in b.outgoing.items():
            if child_index == s.index:
                return "LEFT-ARC-" + edge
        for child_index, edge in s.outgoing.items():
            if child_index == b.index:
                return "RIGHT-ARC-" + edge
        for child_index, edge in b.outgoing.items():# + b.incoming.items():
            if child_index < s.index:
                return "REDUCE"
    return "SHIFT"
"""