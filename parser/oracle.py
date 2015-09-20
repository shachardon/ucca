from action import Action
import layer1

SHIFT = Action("SHIFT")
REDUCE = Action("REDUCE")
SWAP = Action("SWAP")
WRAP = Action("WRAP")
FINISH = Action("FINISH")

ROOT_ID = "1.1"  # ID of root node in UCCA passages


class Oracle:
    """
    Oracle to produce gold transition parses given UCCA passages
    To be used for creating training data for a transition-based UCCA parser
    """
    def __init__(self, passage):
        self.nodes_left = {node.ID for node in passage.layer(layer1.LAYER_ID).all} - {ROOT_ID}
        self.edges_left = {edge for node in passage.nodes.values() for edge in node}
        self.swapped = set()
        self.passage = passage

    def get_action(self, config):
        """
        Determine best action according to current state
        :param config: current Configuration of the parser
        :return: best Action to perform
        """
        if not self.edges_left:
            return FINISH
        if config.stack:
            s = self.passage.by_id(config.stack[-1].node_id)
            edges = self.edges_left.intersection(s.incoming + s.outgoing)
            if not edges:
                return REDUCE
            if len(edges) == 1:
                edge = edges.pop()
                if edge.parent.ID == ROOT_ID:
                    self.edges_left.remove(edge)
                    return Action("ROOT", edge.tag, ROOT_ID)
        if not config.buffer:
            self.swapped = set()
            return WRAP
        b = self.passage.by_id(config.buffer[0].node_id)
        for edge in self.edges_left.intersection(b.incoming):
            if edge.parent.ID in self.nodes_left:
                self.edges_left.remove(edge)
                self.nodes_left.remove(edge.parent.ID)
                return Action("NODE", edge.tag, edge.parent.ID)
        if config.stack:
            for edge in self.edges_left.intersection(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_left.remove(edge)
                    return Action("REMOTE" if edge.attrib.get("remote") else "EDGE",
                                  edge.tag, edge.parent.ID)
            if len(config.stack) > 1:
                s2 = self.passage.by_id(config.stack[-2].node_id)
                pair = frozenset((s, s2))
                if pair not in self.swapped:
                    children = [edge.child.ID for edge in self.edges_left.intersection(s2.outgoing)]
                    parents = [edge.parent.ID for edge in self.edges_left.intersection(s2.incoming)]
                    # FIXME the two lines above should make sense somehow
                    if any(c.node_id in children for c in config.buffer) and not \
                            any(c.node_id in children for c in config.stack) or \
                            any(p.node_id in parents for p in config.stack) and not \
                            any(p.node_id in parents for p in config.buffer):
                        self.swapped.add(pair)
                        return SWAP
        return SHIFT
