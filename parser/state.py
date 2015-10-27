from collections import deque, defaultdict
from itertools import groupby
from operator import attrgetter
import sys

from action import SHIFT, NODE, IMPLICIT, REDUCE, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE, SWAP, FINISH
from config import Config
from ucca.convert import from_text
from ucca import layer0
from ucca import layer1
from ucca import core
from oracle import ROOT_ID


class Node:
    """
    Temporary representation for core.Node with only relevant information for parsing
    """
    def __init__(self, index, node_id=None, text=None, tag=None, implicit=False):
        self.index = index  # Index in the configuration's node list
        self.node_id = node_id  # During training, the ID of the original node
        self.text = text  # Text for terminals, None for non-terminals
        self.tag = tag  # During training, the node tag of the original node (Word/Punctuation)
        self.node_index = int(node_id.split(".")[1]) if node_id else None  # Second part of ID
        self.outgoing = []  # Edge list
        self.incoming = []  # Edge list
        self.node = None  # Instantiated when creating the final Passage: the associated core.Node
        self.implicit = implicit  # True or False

    def add_to_l1(self, l1, parent, tag, terminals):
        """
        Called when creating final Passage to add a new core.Node
        """
        # assert self.node is None or self.text,\
        #     "Trying to create the same node twice: %s, parent: %s" % (self.node_id, parent)
        edge = self.outgoing[0] if len(self.outgoing) == 1 else None
        if self.text:
            if not self.node:  # For punctuation, already created by add_punct for parent
                self.node = parent.node.add(layer1.EdgeTags.Terminal,
                                            terminals[self.index]).child
        elif edge and edge.child.text and layer0.is_punct(terminals[edge.child.index]):
            # assert tag == layer1.EdgeTags.Punctuation, "Tag for %s is %s" % (parent.node_id, tag)
            # assert edge.tag == layer1.EdgeTags.Terminal, "Tag for %s is %s" % (self.node_id, edge.tag)
            self.node = l1.add_punct(parent.node, terminals[edge.child.index])
            edge.child.node = self.node[0].child
        else:  # The usual case
            self.node = l1.add_fnode(parent.node, tag, implicit=self.implicit)
        if self.node and self.node_id:  # We are in training and we have a gold passage
            self.node.extra["remarks"] = self.node_id  # Keep original node ID for reference

    @property
    def is_linkage(self):
        """
        Is this a LKG type node? (During parsing there are no node types)
        """
        return self.outgoing and all(e.tag in (layer1.EdgeTags.LinkRelation,
                                               layer1.EdgeTags.LinkArgument)
                                     for e in self.outgoing)

    def __repr__(self):
        return Node.__name__ + "(" + str(self.index) + \
               ((", " + self.text) if self.text else "") + \
               ((", " + self.node_id) if self.node_id else "") + ")"

    def __str__(self):
        return self.text or self.node_id or str(self.index)

    def __eq__(self, other):
        return self.index == other.index and self.outgoing == other.outgoing

    def __hash__(self):
        return hash((self.index, tuple(self.outgoing)))


class Edge:
    """
    Temporary representation for core.Edge with only relevant information for parsing
    """
    def __init__(self, parent, child, tag, remote=False):
        self.parent = parent  # Node object from which this edge comes
        self.child = child  # Node object to which this edge goes
        self.tag = tag  # String tag
        self.remote = remote  # True or False

    def add(self):
        assert self.tag is not None, "No tag given for new edge %s -> %s" % (self.parent, self.child)
        assert self.parent is not self.child, "Trying to create self-loop edge on %s" % self.parent
        # assert self not in self.parent.outgoing, "Trying to create outgoing edge twice: %s" % self
        # assert self not in self.child.incoming, "Trying to create incoming edge twice: %s" % self
        self.parent.outgoing.append(self)
        self.child.incoming.append(self)
        if Config.verbose:
            print("    %s" % self)

    def __repr__(self):
        return Edge.__name__ + "(" + self.tag + ", " + self.parent + ", " + self.child +\
               ((", " + str(self.remote)) if self.remote else "") + ")"

    def __str__(self):
        return "%s -%s-> %s%s" % (self.parent, self.tag, self.child,
                                  " (remote)" if self.remote else "")

    def __eq__(self, other):
        return self.parent.index == other.parent.index and self.child == other.child and \
               self.tag == other.tag and self.remote == other.remote

    def __hash__(self):
        return hash((self.parent.index, self.child.index, self.tag))


class State:
    """
    The parser's state, responsible for applying actions and creating the final Passage
    :param passage: a Passage object to get the tokens from, or a list of lists of strings
    :param passage_id: the ID of the passage to generate
    """
    def __init__(self, passage, passage_id):
        if isinstance(passage, core.Passage):  # During training, create from gold Passage
            self.nodes = [Node(i, node_id=x.ID, text=x.text, tag=x.tag) for i, x in
                          enumerate(passage.layer(layer0.LAYER_ID).all)]
            self.tokens = [[terminal.text for terminal in terminals]
                           for _, terminals in groupby(passage.layer(layer0.LAYER_ID).all,
                                                       key=attrgetter('paragraph'))]
        else:  # During parsing, create from plain text: assume passage is list of lists of strings
            self.tokens = passage
            self.nodes = [Node(i, text=token) for i, token in
                          enumerate(token for paragraph in passage for token in paragraph)]
        self.terminals = list(self.nodes)
        self.buffer = deque(self.nodes)
        self.root = self.add_node(ROOT_ID)  # The root is not part of the stack/buffer
        self.stack = [self.root]
        self.passage_id = passage_id

    def legal_actions(self):
        """
        :return: all action types applicable in the current state
        """
        yield FINISH
        if self.buffer:
            yield SHIFT
        if self.stack:
            yield NODE
            yield IMPLICIT
            yield REDUCE
            if len(self.stack) > 1:
                yield LEFT_EDGE
                yield RIGHT_EDGE
                yield LEFT_REMOTE
                yield RIGHT_REMOTE
                if Config.compoundswap:
                    for i in range(1, len(self.stack)):
                        yield SWAP(i)
                else:
                    yield SWAP

    def is_legal(self, action):
        """
        :return: is the action (with its tag) legal in the current state?
        """
        return action in self.legal_actions() and \
               (action not in (LEFT_EDGE, LEFT_REMOTE) or
                self.create_edge(action) not in self.stack[-1].outgoing) and \
               (action not in (RIGHT_EDGE, RIGHT_REMOTE) or
                self.create_edge(action) not in self.stack[-2].outgoing)

    def apply_action(self, action):
        """
        Main part of the parser: apply action given by oracle or classifier
        :param action: Action object to apply
        :return: True if parsing should continue, False if finished
        """
        if Config.verify:
            assert action in self.legal_actions(), "Illegal action in current state: %s" % action
        if action == SHIFT:  # Push buffer head to stack; shift buffer
            self.stack.append(self.buffer.popleft())
        elif action == NODE:  # Create new parent node and add to the buffer
            parent = self.add_node(action.node_id)
            Edge(parent, self.stack[-1], action.tag).add()
            self.buffer.appendleft(parent)
        elif action == IMPLICIT:  # Create new child node and add to the buffer
            child = self.add_node(action.node_id, implicit=True)
            Edge(self.stack[-1], child, action.tag).add()
            self.buffer.appendleft(child)
        elif action == REDUCE:  # Pop stack (no more edges to create with this node)
            self.stack.pop()
        elif action in (LEFT_EDGE, LEFT_REMOTE, RIGHT_EDGE, RIGHT_REMOTE):
            self.create_edge(action).add()
        elif action == SWAP:  # Place second (or more) stack item back on the buffer
            distance = action.tag or 1
            assert distance > 0
            s = slice(-distance-1, -1)
            if Config.verbose:
                print("    %s <--> %s" % (", ".join(map(str, self.stack[s])), self.stack[-1]))
            self.buffer.extendleft(reversed(self.stack[s]))  # extendleft reverses the order
            del self.stack[s]
        elif action == FINISH:  # Nothing left to do
            return False
        else:
            raise Exception("Invalid action: " + action)
        # intersection = set(self.stack).intersection(self.buffer)
        # assert not intersection, "Stack and buffer overlap: %s" % intersection
        return True

    def add_node(self, *args, **kwargs):
        """
        Called during parsing to add a new Node (not core.Node) to the temporary representation
        """
        node = Node(len(self.nodes), *args, **kwargs)
        self.nodes.append(node)
        if Config.verbose:
            print("    %s" % node)
        return node

    def create_edge(self, action):
        if action == LEFT_EDGE:  # Create left edge between buffer top two nodes
            return Edge(self.stack[-1], self.stack[-2], action.tag)
        elif action == RIGHT_EDGE:  # Create right edge between buffer top two nodes
            return Edge(self.stack[-2], self.stack[-1], action.tag)
        elif action == LEFT_REMOTE:  # Same as LEFT-EDGE but a remote edge is created
            return Edge(self.stack[-1], self.stack[-2], action.tag, remote=True)
        elif action == RIGHT_REMOTE:  # Same as RIGHT-EDGE but a remote edge is created
            return Edge(self.stack[-2], self.stack[-1], action.tag, remote=True)

    def create_passage(self):
        """
        Create final passage from temporary representation
        :return: core.Passage created from self.nodes
        """
        paragraphs = [" ".join(paragraph) for paragraph in self.tokens]
        passage = from_text(paragraphs, self.passage_id)
        terminals = passage.layer(layer0.LAYER_ID).all
        self.fix_terminal_tags(terminals)
        l1 = layer1.Layer1(passage)
        if self.root.node_id:  # We are in training and we have a gold passage
            passage.nodes[ROOT_ID].extra["remarks"] = self.root.node_id  # For reference
        remotes = []  # To be handled after all nodes are created
        linkages = []  # To be handled after all non-linkage nodes are created
        self.topological_sort()  # Sort self.nodes
        for node in self.nodes:
            assert node.text or node.outgoing or node.implicit, "Non-terminal leaf node: %s" % node
            assert node.node or node is self.root or node.is_linkage, "Non-root without incoming: %s" % node
            if node.is_linkage:
                linkages.append(node)
            else:
                for edge in node.outgoing:
                    if edge.remote:
                        remotes.append((node, edge))
                    else:
                        edge.child.add_to_l1(l1, node, edge.tag, terminals)

        for node, edge in remotes:  # Add remote edges
            node.node.add(edge.tag, edge.child.node, edge_attrib={"remote": True})

        for node in linkages:  # Add linkage nodes and edges
            link_relation = None
            link_args = []
            for edge in node.outgoing:
                if edge.tag == layer1.EdgeTags.LinkRelation:
                    assert link_relation is None, "Multiple link relations: %s, %s" % (link_relation, edge.child.node)
                    link_relation = edge.child.node
                elif edge.tag == layer1.EdgeTags.LinkArgument:
                    link_args.append(edge.child.node)
            assert link_relation is not None, "No link relations: %s" % node
            # assert len(link_args) > 1, "Less than two link arguments"
            node.node = l1.add_linkage(link_relation, *link_args)
            if node.node_id:  # We are in training and we have a gold passage
                node.node.extra["remarks"] = node.node_id  # For reference

        return passage

    def fix_terminal_tags(self, terminals):
        for terminal, orig_terminal in zip(terminals, self.terminals):
            if terminal.tag != orig_terminal.tag:
                if Config.verbose:
                    print("%s is the wrong tag for terminal: %s" % (terminal.tag, terminal.text),
                          file=sys.stderr)
                terminal.tag = orig_terminal.tag

    def topological_sort(self):
        """
        Sort self.nodes topologically, each node appearing as early as possible
        Also sort each node's outgoing and incoming edge according to the node order
        """
        levels = defaultdict(list)
        level_by_index = {}
        stack = [node for node in self.nodes if not node.outgoing]
        while stack:
            node = stack.pop()
            if node.index not in level_by_index:
                parents = [edge.parent for edge in node.incoming]
                if parents:
                    unexplored_parents = [parent for parent in parents
                                          if parent.index not in level_by_index]
                    if unexplored_parents:
                        for parent in unexplored_parents:
                            stack.append(node)
                            stack.append(parent)
                    else:
                        level = 1 + max(level_by_index[parent.index] for parent in parents)
                        levels[level].append(node)
                        level_by_index[node.index] = level
                else:
                    levels[0].append(node)
                    level_by_index[node.index] = 0
        self.nodes = [node for level, level_nodes in sorted(levels.items())
                      for node in sorted(level_nodes, key=lambda x: x.node_index or x.index)]
        for node in self.nodes:
            node.outgoing.sort(key=lambda x: x.child.node_index or self.nodes.index(x.child))
            node.incoming.sort(key=lambda x: x.parent.node_index or self.nodes.index(x.parent))

    def str(self, sep):
        return "stack: [%-20s]%sbuffer: [%s]" % (" ".join(map(str, self.stack)), sep,
                                                 " ".join(map(str, self.buffer)))

    def __str__(self):
        return self.str(" ")

    def __eq__(self, other):
        return self.stack == other.stack and self.buffer == other.buffer and \
               self.nodes == other.nodes

    def __hash__(self):
        return hash((tuple(self.stack), tuple(self.buffer), tuple(self.nodes)))
