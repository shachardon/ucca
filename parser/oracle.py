from action import Action, SHIFT, REDUCE, FINISH
from config import COMPOUND_SWAP
from ucca import layer1

ROOT_ID = "1.1"  # ID of root node in UCCA passages


class Oracle:
    """
    Oracle to produce gold transition parses given UCCA passages
    To be used for creating training data for a transition-based UCCA parser
    :param passage gold passage to get the correct edges from
    """
    def __init__(self, passage):
        self.nodes_remaining = {node.ID for node in passage.layer(layer1.LAYER_ID).all} - {ROOT_ID}
        self.edges_remaining = {edge for node in passage.nodes.values() for edge in node}
        self.passage = passage

    def get_action(self, state):
        """
        Determine best action according to current state
        :param state: current State of the parser
        :return: best Action to perform
        """
        if not self.edges_remaining:
            return FINISH

        stack = [self.passage.by_id(node.node_id) for node in state.stack]
        if stack:
            incoming = self.edges_remaining.intersection(stack[-1].incoming)
            outgoing = self.edges_remaining.intersection(stack[-1].outgoing)
            edges = incoming | outgoing
            if not edges:
                return REDUCE

            related = set([edge.child.ID for edge in outgoing] +
                          [edge.parent.ID for edge in incoming])
            # prefer incorporating immediate relatives if possible
            if state.buffer and state.buffer[0].node_id in related:
                return SHIFT

            if len(stack) > 1:
                # check for binary edges
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
                # check if a swap is necessary, and how far (if compound swap is enabled)
                swap_distance = 0
                while len(stack) > swap_distance + 1 and (COMPOUND_SWAP or swap_distance < 1) and \
                        related.intersection(s.ID for s in stack[:-swap_distance-2]) and \
                        not related.intersection(b.node_id for b in state.buffer):
                    swap_distance += 1
                if swap_distance:
                    return Action("SWAP", swap_distance if COMPOUND_SWAP else None)

            # check for unary edges
            for edges, prefix, attr in (((e for e in incoming if
                                          e.parent.ID in self.nodes_remaining and not e.attrib.get("remote")),
                                         "NODE", "parent"),
                                        ((e for e in outgoing if
                                          e.child.attrib.get("implicit")),
                                         "IMPLICIT", "child")):
                for edge in edges:
                    self.edges_remaining.remove(edge)
                    node_id = getattr(edge, attr).ID
                    self.nodes_remaining.remove(node_id)
                    return Action(prefix, edge.tag, node_id)

        if not state.buffer:
            raise Exception("No action is possible\n" + state.str("\n") + "\n" + self.str("\n"))

        return SHIFT

    def str(self, sep):
        return "nodes left: [%s]%sedges left: [%s]" % (" ".join(self.nodes_remaining), sep,
                                                       " ".join(map(str, self.edges_remaining)))

    def __str__(self):
        return str(" ")
