import re
from collections import deque, defaultdict
import argparse
import sys
from operator import attrgetter
from itertools import groupby

import numpy as np
from diff import diff_passages

from ucca import layer0, layer1
from ucca.core import Passage
from ucca.convert import from_text
from scripts.util import file2passage, passage2file
from oracle import Oracle, ROOT_ID

desc = """Transition-based parser for UCCA.
"""


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
        if isinstance(passage, Passage):  # During training, create from gold Passage
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

    def apply_action(self, action, node_id=None):
        """
        Main part of the parser: apply action given by oracle or classifier
        :param action: string representing action to apply (with tag if needed)
        :param node_id: during training, created node ID from gold passage (if action creates one)
        :return: True if parsing should continue, False if finished
        """
        m = re.match("(.*)-(.*)", action)
        if m:  # Action contains tag
            action_type, tag = m.groups()
            if action_type == "NODE":  # Create new node and push to the stack
                parent = self.add_node(node_id)
                parent.add_edge(self.buffer[0], tag)
                self.stack.append(parent)
            elif action_type == "EDGE":  # Create edge between stack top and buffer head
                self.stack[-1].add_edge(self.buffer[0], tag)
            elif action_type == "REMOTE":  # Same as EDGE but a remote edge is created
                self.stack[-1].add_edge(self.buffer[0], tag, remote=True)
            elif action_type == "ROOT":  # Create edge between stack top and ROOT; pop stack
                self.root.add_edge(self.stack.pop(), tag)
            else:
                raise Exception("Invalid action: " + action_type + " with tag " + tag)
        elif action == "REDUCE":  # Pop stack (no more edges to create with this node)
            self.stack.pop()
        elif action == "SHIFT":  # Push buffer head to stack; shift buffer
            self.stack.append(self.buffer.popleft())
        elif action == "SWAP":  # Swap top two stack elements (to handle non-projective edge)
            self.stack.append(self.stack.pop(-2))
        elif action == "WRAP":  # Buffer exhausted but not finished yet: wrap stack back to buffer
            self.buffer = deque(self.stack)
            self.stack = []
        elif action == "FINISH":  # Nothing left to do
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


class Parser:
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self):
        self.config = None  # Configuration object created at each parse
        self.actions = [action + relation for action in ("NODE-", "EDGE-", "REMOTE-", "ROOT-")
                        for name, relation in layer1.EdgeTags.__dict__.items()
                        if isinstance(relation, str) and not name.startswith('__')] +\
                       ["REDUCE", "SHIFT", "SWAP", "WRAP", "FINISH"]
        self.actions_reverse = {action: i for i, action in enumerate(self.actions)}
        self.features = [
            lambda: len(self.config.stack),
            lambda: len(self.config.buffer)
        ]
        self.weights = 0.01 * np.random.randn(len(self.actions), len(self.features))

    def feature_array(self):
        """
        Calculate features according to current configuration
        :return: NumPy array with all feature values
        """
        return np.array([f() for f in self.features])

    def train(self, passages, iterations=1):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        """
        print("%d training passages" % len(passages))
        for iteration in range(iterations):
            print("Iteration %d" % iteration)
            correct = 0
            actions = 0
            for passage in passages:
                self.config = Configuration(passage, passage.ID)
                oracle = Oracle(passage)
                while True:
                    pred_action = self.predict_action()
                    true_action, node_id = oracle.get_action(self.config)
                    if not self.update(pred_action, true_action):
                        correct += 1
                    # print("  predicted: %-15s true: %-15s stack: %-20s buffer: %-70s" %
                    print("  %-15s stack: %-40s buffer: %-70s" %
                          (true_action, self.config.stack, list(self.config.buffer)))
                    actions += 1
                    if not self.config.apply_action(true_action, node_id):
                        break
                print("  stack: %-40s buffer: %-70s" %
                      (self.config.stack, list(self.config.buffer)))
                out_f = "%s/%s%s.xml" % (args.outdir, args.prefix, passage.ID)
                sys.stderr.write("Writing passage '%s'...\n" % out_f)
                pred_passage = self.config.passage
                passage2file(pred_passage, out_f)
                assert passage.equals(pred_passage), "Oracle failed to produce true passage\n" + \
                                                     diff_passages(passage, pred_passage)
            print("Accuracy: %.3f (%d/%d)\n" % (correct/actions, correct, actions)
                  if actions else "No actions done")

    def parse(self, passages):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :return: generator of parsed passages
        """
        print("%d passages to parse" % len(passages))
        for passage in passages:
            self.config = Configuration(passage, passage.ID)
            while self.config.apply_action(self.predict_action()):
                pass
            yield self.config.passage

    def predict_action(self):
        """
        Choose action based on classifier
        :return: action with maximum probability according to classifier
        """
        features = self.feature_array()
        return self.actions[np.argmax(self.weights.dot(features))]

    def update(self, pred_action, true_action):
        """
        Update classifier weights according to predicted and true action
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :return: True if update was needed, False if predicted and true actions were the same
        """
        if pred_action == true_action:
            return False
        features = self.feature_array()
        self.weights[self.actions_reverse[true_action]] += features
        self.weights[self.actions_reverse[pred_action]] -= features
        return True


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('train', nargs='+', help="passage file names to train on")
    argparser.add_argument('-t', '--test', nargs='+', help="passage file names to test on")
    argparser.add_argument('-o', '--outdir', default='.', help="output directory")
    argparser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
    args = argparser.parse_args()

    train_passages = [file2passage(filename) for filename in args.train]
    test_passages = [file2passage(filename) for filename in args.test] if args.test else []
    parser = Parser()
    parser.train(train_passages)
    # for pred_passage in parser.parse(test_passages):
    #     outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
    #     sys.stderr.write("Writing passage '%s'...\n" % outfile)
    #     passage2file(pred_passage, outfile)
