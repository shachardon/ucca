from collections import deque, defaultdict
from itertools import groupby
from operator import attrgetter

from convert import from_text
from ucca import layer0
from ucca import layer1
from ucca import core
from oracle import ROOT_ID

__author__ = 'danielh'


class Node:
    """
    Temporary representation for core.Node with only relevant information for parsing
    """
    def __init__(self, index, text=None, node_id=None):
        self.index = index  # Index in the configuration's node list
        self.text = text  # Text for terminals, None for non-terminals
        self.node_id = node_id  # During training, the ID of the original node
        self.node_index = int(node_id.split(".")[1]) if node_id else None  # Second part of ID
        self.outgoing = []  # Edge list
        self.incoming = []  # Edge list
        self.node = None  # Instantiated when creating the final Passage: the associated core.Node

    def __repr__(self):
        return self.text or self.node_id or "Node(%d)" % self.index

    def add_edge(self, child, tag, remote=False):
        """
        Called during parsing to add a new Edge (not core.Edge) to the temporary representation
        """
        assert tag is not None, "No tag given for new edge"
        assert self != child, "Trying to create self-loop edge"
        assert not any(e.node == child for e in self.outgoing), "Trying to create edge twice"
        assert not any(e.node == self for e in child.incoming), "Trying to create edge twice"
        self.outgoing.append(Edge(tag, child, remote))
        child.incoming.append(Edge(tag, self, remote))
        print("    %s->%s%s" % (tag, child, " (remote)" if remote else ""))

    def add_layer1_node(self, l1, parent, tag, terminals):
        """
        Called when creating final Passage to add a new core.Node
        """
        assert self.node is None or self.text, "Trying to create the same node twice"
        if self.text:
            if not self.node:  # For punctuation, already created by add_punct for parent
                self.node = parent.node.add(layer1.EdgeTags.Terminal,
                                            terminals[self.index]).child
        elif len(self.outgoing) == 1 and self.outgoing[0].node.text and \
                layer0.is_punct(terminals[self.outgoing[0].node.index]):
            assert tag == layer1.EdgeTags.Punctuation
            assert self.outgoing[0].tag == layer1.EdgeTags.Terminal
            self.node = l1.add_punct(parent.node, terminals[self.outgoing[0].node.index])
            self.outgoing[0].node.node = self.node[0].child
        else:  # The usual case
            self.node = l1.add_fnode(parent.node, tag)
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


class Edge:
    """
    Temporary representation for core.Edge with only relevant information for parsing
    """
    def __init__(self, tag, node, remote=False):
        self.tag = tag
        self.node = node
        self.remote = remote


class Configuration:
    """
    The parser's state, responsible for applying actions and creating the final Passage
    """
    def __init__(self, passage, passage_id):
        if isinstance(passage, core.Passage):  # During training, create from gold Passage
            self.nodes = [Node(i, text=x.text, node_id=x.ID) for i, x in
                          enumerate(passage.layer(layer0.LAYER_ID).all)]
            self.tokens = [[x.text for x in xs]
                           for _, xs in groupby(passage.layer(layer0.LAYER_ID).all,
                                                key=attrgetter('paragraph'))]
            self.root_id = ROOT_ID
        else:  # During parsing, create from plain text: assume passage is list of lists of strings
            self.tokens = [token for paragraph in passage for token in paragraph]
            self.nodes = [Node(i, text=x) for i, x in enumerate(self.tokens)]
            self.root_id = None
        self.buffer = deque(self.nodes)
        self.stack = []
        self.root = self.add_node(self.root_id)  # The root is not part of the stack/buffer
        self.passage_id = passage_id

    def apply_action(self, action):
        """
        Main part of the parser: apply action given by oracle or classifier
        :param action: Action object to apply
        :return: True if parsing should continue, False if finished
        """
        if action.type == "NODE":  # Create new node and push to the stack
            parent = self.add_node(action.node_id)
            parent.add_edge(self.buffer[0], action.tag)
            self.stack.append(parent)
        elif action.type == "EDGE":  # Create edge between stack top and buffer head
            self.stack[-1].add_edge(self.buffer[0], action.tag)
        elif action.type == "REMOTE":  # Same as EDGE but a remote edge is created
            self.stack[-1].add_edge(self.buffer[0], action.tag, remote=True)
        elif action.type == "ROOT":  # Create edge between stack top and ROOT; pop stack
            self.root.add_edge(self.stack.pop(), action.tag)
        elif action.type == "REDUCE":  # Pop stack (no more edges to create with this node)
            self.stack.pop()
        elif action.type == "SHIFT":  # Push buffer head to stack; shift buffer
            self.stack.append(self.buffer.popleft())
        elif action.type == "SWAP":  # Swap top two stack elements (to handle non-projective edge)
            self.stack.append(self.stack.pop(-2))
        elif action.type == "WRAP":  # Buffer exhausted but not finished yet: wrap stack back to buffer
            self.buffer = deque(self.stack)
            self.stack = []
        elif action.type == "FINISH":  # Nothing left to do
            return False
        else:
            raise Exception("Invalid action: " + action)
        assert not set(self.stack).intersection(self.buffer), "Stack and buffer overlap"
        return True

    def add_node(self, node_id=None):
        """
        Called during parsing to add a new Node (not core.Node) to the temporary representation
        """
        node = Node(len(self.nodes), node_id=node_id)
        self.nodes.append(node)
        print("    %s" % node)
        return node

    @property
    def passage(self):
        """
        Create final passage from temporary representation
        :return: core.Passage created from self.nodes
        """
        paragraphs = [" ".join(paragraph) for paragraph in self.tokens]
        passage = from_text(paragraphs, self.passage_id)
        terminals = passage.layer(layer0.LAYER_ID).all
        l1 = layer1.Layer1(passage)
        if self.root.node_id:  # We are in training and we have a gold passage
            passage.nodes[ROOT_ID].extra["remarks"] = self.root.node_id  # For reference
        remotes = []  # To be handled after all nodes are created
        linkages = []  # To be handled after all non-linkage nodes are created
        self.topological_sort()  # Sort self.nodes
        for node in self.nodes:
            assert node.text or node.outgoing, "Non-terminal leaf node"
            assert node.node or node == self.root or node.is_linkage, "Non-root without incoming"
            for edge in node.outgoing:
                if edge.remote:
                    remotes.append((node, edge))
                elif node.is_linkage:
                    linkages.append(node)
                else:  # The usual case
                    edge.node.add_layer1_node(l1, node, edge.tag, terminals)

        for node, edge in remotes:  # Add remote edges
            node.node.add(edge.tag, edge.node.node, edge_attrib={"remote": True})

        for node in linkages:  # Add linkage nodes and edges
            link_relation = None
            link_args = []
            for edge in node.outgoing:
                if edge.tag == layer1.EdgeTags.LinkRelation:
                    assert link_relation is None, "Multiple link relations"
                    link_relation = edge.node.node
                elif edge.tag == layer1.EdgeTags.LinkArgument:
                    link_args.append(edge.node.node)
            assert link_relation is not None, "No link relations"
            assert len(link_args) > 1, "Less than two link arguments"
            node.node = l1.add_linkage(link_relation, *link_args)
            if node.node_id:  # We are in training and we have a gold passage
                node.node.extra["remarks"] = node.node_id  # For reference

        return passage

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
                parents = [edge.node for edge in node.incoming]
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
            node.outgoing.sort(key=lambda x: x.node.node_index or self.nodes.index(x.node))
            node.incoming.sort(key=lambda x: x.node.node_index or self.nodes.index(x.node))