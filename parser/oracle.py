from action import Action
from ucca import layer1

SHIFT = Action("SHIFT")
REDUCE = Action("REDUCE")
FINISH = Action("FINISH")

ROOT_ID = "1.1"  # ID of root node in UCCA passages


class Oracle:
    """
    Oracle to produce gold transition parses given UCCA passages
    To be used for creating training data for a transition-based UCCA parser
    :param passage gold passage to get the correct edges from
    :param compound_swap whether to allow swap actions that move i steps rather than 1
    """
    def __init__(self, passage, compound_swap=False):
        self.nodes_remaining = {node.ID for node in passage.layer(layer1.LAYER_ID).all} - {ROOT_ID}
        self.edges_remaining = {edge for node in passage.nodes.values() for edge in node}
        self.swapped = set()
        self.passage = passage
        self.compound_swap = compound_swap

    def get_action(self, state):
        """
        Determine best action according to current state
        :param state: current State of the parser
        :return: best Action to perform
        """
        if not self.edges_remaining:
            return FINISH
        stack = [self.passage.by_id(node.node_id) for node in state.stack]
        buffer = [self.passage.by_id(node.node_id) for node in state.buffer]
        if stack:
            incoming = self.edges_remaining.intersection(stack[-1].incoming)
            outgoing = self.edges_remaining.intersection(stack[-1].outgoing)
            edges = incoming | outgoing
            related = set([edge.child.ID for edge in outgoing] +
                          [edge.parent.ID for edge in incoming])
            if not edges:
                return REDUCE
            if len(edges) == 1:
                edge = edges.pop()
                if edge.parent.ID == ROOT_ID:
                    self.edges_remaining.remove(edge)
                    return Action("ROOT", edge.tag, ROOT_ID)
            if buffer and buffer[0].ID in related:
                return SHIFT
            for edges, attr, prefix in (((e for e in incoming if
                                          e.parent.ID in self.nodes_remaining and not e.attrib.get("remote")),
                                         "parent", "NODE"),
                                        ((e for e in outgoing if
                                          e.child.attrib.get("implicit")),
                                         "child", "IMPLICIT")):
                for edge in edges:
                    self.edges_remaining.remove(edge)
                    node_id = getattr(edge, attr).ID
                    self.nodes_remaining.remove(node_id)
                    return Action(prefix, edge.tag, node_id)
            if len(stack) > 1:
                for edges, prefix in (((e for e in incoming if
                                        e.parent.ID == stack[-2].ID),
                                       "RIGHT"),
                                      ((e for e in outgoing if
                                        e.child.ID == stack[-2].ID),
                                       "LEFT")):
                    for edge in edges:
                        self.edges_remaining.remove(edge)
                        return Action(prefix + ("-REMOTE" if edge.attrib.get("remote") else "-EDGE"),
                                      edge.tag)
                swap_distance = self.check_swap_distance(stack, buffer, related)
                if swap_distance:
                    return Action("SWAP", swap_distance if self.compound_swap else None)
        return SHIFT

    def check_swap_distance(self, stack, buffer, related):
        """
        Check if a swap is required, and to what distance (how many items to move to buffer)
        :return: 0 if no swap required, 1 if compound_swap is False, swap distance otherwise
        """
        distance = 0
        while len(stack) > distance + 1 and (self.compound_swap or distance < 1):
            pair = frozenset((stack[-1].ID, stack[-distance-2].ID))
            if pair in self.swapped:
                break
            if related.intersection(s.ID for s in stack[:-distance-2]) and \
                    not related.intersection(b.ID for b in buffer):
                self.swapped.add(pair)
                distance += 1
            else:
                break
        return distance

    def str(self, sep):
        return "nodes left: [%s]%sedges left: [%s]" % (" ".join(self.nodes_remaining), sep,
                                                       " ".join(map(str, self.edges_remaining)))

    def __str__(self):
        return str(" ")
