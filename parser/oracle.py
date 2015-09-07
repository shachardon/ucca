from action import Action

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
        self.nodes_created = {ROOT_ID}
        self.edges_created = set()
        self.swapped = set()
        self.passage = passage

    def get_action(self, config):
        """
        Determine best action according to current state
        :param config: current Configuration of the parser
        :return: best Action to perform
        """
        if not config.stack and not config.buffer or \
                self.nodes_created == set(self.passage.nodes):
            return FINISH
        if config.stack:
            s = self.passage.by_id(config.stack[-1].node_id)
            remaining = self.remaining(s.incoming + s.outgoing)
            if not remaining:
                return REDUCE
            if len(remaining) == 1 and remaining[0].parent.ID == ROOT_ID:
                self.edges_created.add(remaining[0])
                return Action("ROOT", remaining[0].tag, ROOT_ID)
        if config.buffer:
            b = self.passage.by_id(config.buffer[0].node_id)
            for edge in self.remaining(b.incoming):
                if edge.parent.ID not in self.nodes_created:
                    self.edges_created.add(edge)
                    self.nodes_created.add(edge.parent.ID)
                    return Action("NODE", edge.tag, edge.parent.ID)
        else:
            self.swapped = set()
            return WRAP
        if config.stack and config.buffer:
            for edge in self.remaining(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_created.add(edge)
                    action_type = "REMOTE" if edge.attrib.get("remote") else "EDGE"
                    return Action(action_type, edge.tag, edge.parent.ID)
            if len(config.stack) > 1:
                s2 = self.passage.by_id(config.stack[-2].node_id)
                if (s, s2) not in self.swapped and \
                        set([c.ID for c in s2.children]).intersection(
                        [c.node_id for c in config.buffer]):
                    self.swapped.add((s, s2))
                    self.swapped.add((s2, s))
                    return SWAP
        return SHIFT

    def remaining(self, edges):
        return [e for e in edges if e not in self.edges_created]