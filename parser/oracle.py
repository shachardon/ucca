from action import Action, SHIFT, NODE, IMPLICIT, REDUCE, SWAP, FINISH
from config import Config
from constants import ROOT_ID
from ucca import layer1


class Oracle(object):
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

        if state.stack:
            s0 = state.stack[-1]
            incoming = self.edges_remaining.intersection(s0.orig_node.incoming)
            outgoing = self.edges_remaining.intersection(s0.orig_node.outgoing)
            if not incoming and not outgoing:
                return REDUCE

            related = set([edge.child.ID for edge in outgoing] +
                          [edge.parent.ID for edge in incoming])
            # Prefer incorporating immediate relatives if possible
            if state.buffer and state.buffer[0].node_id in related:
                return SHIFT

            if len(state.stack) > 1:
                s1 = state.stack[-2]
                # Check for binary edges
                for edges, prefix in (((e for e in incoming if
                                        e.parent.ID == s1.node_id),
                                       "RIGHT"),
                                      ((e for e in outgoing if
                                        e.child.ID == s1.node_id),
                                       "LEFT")):
                    for edge in edges:
                        self.edges_remaining.remove(edge)
                        return Action(prefix + ("-REMOTE" if edge.attrib.get("remote") else "-EDGE"),
                                      edge.tag)

                # Check if a swap is necessary, and how far (if compound swap is enabled)
                distance = None  # Swap distance (how many nodes in the stack to swap)
                related_in_stack = 0  # How many nodes in the stack are related to the stack top
                for i, s in enumerate(state.stack[-3::-1]):  # Skip top two, they are not related
                    if s.node_id in related:
                        if distance is None and Config().compound_swap:
                            distance = i + 1
                        related_in_stack += 1
                        if related_in_stack == len(related):  # All related nodes are in the stack
                            return SWAP(distance)

            # Check for unary edges
            for edges, action, attr in (((e for e in incoming if
                                          e.parent.ID in self.nodes_remaining and not e.attrib.get("remote")),
                                         NODE, "parent"),
                                        ((e for e in outgoing if
                                          e.child.attrib.get("implicit")),
                                         IMPLICIT, "child")):
                for edge in edges:
                    self.edges_remaining.remove(edge)
                    node = getattr(edge, attr)
                    self.nodes_remaining.remove(node.ID)
                    return action(edge.tag, node)

        if not state.buffer:
            if Config().verify:
                raise Exception("No action is possible\n" + state.str("\n") + "\n" + self.str("\n"))
            else:
                return FINISH

        return SHIFT

    def str(self, sep):
        return "nodes left: [%s]%sedges left: [%s]" % (" ".join(self.nodes_remaining), sep,
                                                       " ".join(map(str, self.edges_remaining)))

    def __str__(self):
        return str(" ")
