"""
Oracle to produce gold transition parses given UCCA passages.
To be used for creating training and test data for a transition-based UCCA parser.
Implements the arc-eager algorithm.
"""


class Oracle:
    def __init__(self, passage):
        self.nodes_created = set(["1.1"])
        self.edges_created = set()
        self.passage = passage

    def get_action(self, config):
        if not config.stack and not config.buffer or \
                self.nodes_created == set(self.passage.nodes):  # FIXME handle missing edges
            return "FINISH", None
        if config.stack:
            s = self.passage.by_id(config.stack[-1].node_id)
            if not self.filter_created(s.incoming + s.outgoing):
                return "REDUCE", None
        if config.buffer:
            b = self.passage.by_id(config.buffer[0].node_id)
            for edge in self.filter_created(b.incoming):
                if edge.parent.ID not in self.nodes_created:
                    self.edges_created.add(edge)
                    self.nodes_created.add(edge.parent.ID)
                    return "NODE-" + edge.tag, edge.parent.ID
        else:
            return "WRAP", None
        if config.stack and config.buffer:
            for edge in self.filter_created(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_created.add(edge)
                    return "EDGE-" + edge.tag, edge.parent.ID
        # TODO return "SWAP", None if there is an edge to create from s to something further along the buffer.
        return "SHIFT", None

    def filter_created(self, edges):
        return [e for e in edges if e not in self.edges_created and e.tag[0] != "L"]  # FIXME handle linkage


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