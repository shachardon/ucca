"""
Oracle to produce gold transition parses given UCCA passages.
To be used for creating training and test data for a transition-based UCCA parser.
Implements the arc-eager algorithm.
"""

import layer1

ROOT_ID = "1.1"


class Oracle:
    def __init__(self, passage):
        self.nodes_created = {ROOT_ID}
        self.edges_created = set()
        self.passage = passage

    def get_action(self, config):
        if not config.stack and not config.buffer or \
                self.nodes_created == set(self.passage.nodes):  # FIXME handle missing edges
            return "FINISH", None
        if config.stack:
            s = self.passage.by_id(config.stack[-1].node_id)
            remaining = self.remaining(s.incoming + s.outgoing)
            if not remaining:
                return "REDUCE", None
            if len(remaining) == 1 and not remaining[0].parent.incoming:
                self.edges_created.add(remaining[0])
                return "ROOT-" + remaining[0].tag, ROOT_ID
        if config.buffer:
            b = self.passage.by_id(config.buffer[0].node_id)
            for edge in self.remaining(b.incoming):
                if edge.parent.ID not in self.nodes_created:
                    self.edges_created.add(edge)
                    self.nodes_created.add(edge.parent.ID)
                    return "NODE-" + edge.tag, edge.parent.ID
        else:
            return "WRAP", None
        if config.stack and config.buffer:
            for edge in self.remaining(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_created.add(edge)
                    return "EDGE-" + edge.tag, edge.parent.ID
            if len(config.stack) > 1:
                s2_id = config.stack[-2].node_id
                # if self.cmp(config.stack + list(config.buffer))(s.ID, s2_id) < 0:
                #     return "SWAP", None
        return "SHIFT", None

    def remaining(self, edges):
        return [e for e in edges if e not in self.edges_created and
                e.tag not in (layer1.EdgeTags.LinkRelation, layer1.EdgeTags.LinkArgument) and
                not e.attrib.get('remote')]  # FIXME handle remote and linkage?

    def cmp(self, nodes):
        units = [self.passage.by_id(node.node_id) for node in nodes]
        levels = {}
        remaining = [u for u in units if not self.remaining(u.outgoing)]
        while remaining:
            u = remaining.pop()
            if u.ID not in levels:
                parents = [e.parent for e in self.remaining(u.incoming)]
                if parents:
                    unexplored_parents = [p for p in parents if p.ID not in levels]
                    if unexplored_parents:
                        for p in unexplored_parents:
                            remaining.append(u)
                            remaining.append(p)
                    else:
                        levels[u.ID] = 1 + max(levels[p.ID] for p in parents)
                else:
                    levels[u.ID] = 0
        return lambda id1, id2: levels[id1] - levels[id2]


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