desc = """Transition-based parser for UCCA.
"""

import re
from collections import deque
import argparse
import sys
from operator import attrgetter
from itertools import groupby

import numpy as np

from ucca import layer0, layer1
from ucca.core import Passage
from ucca.convert import from_text
from scripts.util import file2passage, passage2file
from oracle import Oracle


class Configuration:

    class Node:
        def __init__(self, index, text=None, node_id=None):
            self.index = index
            self.text = text
            self.node_id = node_id
            self.outgoing = {}
            self.incoming = {}
            self.node = None

        def __repr__(self):
            return self.text or self.node_id or "Node(%d)" % self.index

        def add_edge(self, child, tag):
            self.outgoing[child.index] = tag
            child.incoming[self.index] = tag
            print("    %s->%s" % (tag, child))

    def __init__(self, passage, passage_id):
        if isinstance(passage, Passage):
            self.nodes = [Configuration.Node(i, text=x.text, node_id=x.ID) for i, x in
                          enumerate(passage.layer(layer0.LAYER_ID).all)]
            self.tokens = [[x.text for x in xs]
                           for _, xs in groupby(passage.layer(layer0.LAYER_ID).all,
                                                key=attrgetter('paragraph'))]
        else:
            self.tokens = [token for paragraph in passage for token in paragraph]
            self.nodes = [Configuration.Node(i, text=x) for i, x in enumerate(self.tokens)]
        self.buffer = deque(self.nodes)
        self.stack = [self.add_node("1.1")]
        self.passage_id = passage_id

    def apply_action(self, action, node_id=None):
        m = re.match("(.*)-(.*)", action)
        if m:
            action_type, tag = m.groups()
            if action_type == "NODE":
                parent = self.add_node(node_id)
                parent.add_edge(self.buffer[0], tag)
                self.stack.append(parent)
            elif action_type == "EDGE":
                self.stack[-1].add_edge(self.buffer[0], tag)
            else:
                raise Exception("Invalid action: " + action_type)
        elif action == "REDUCE":
            self.stack.pop()
        elif action == "SHIFT":
            self.stack.append(self.buffer.popleft())
        elif action == "WRAP":
            self.buffer = deque(self.stack)
            self.stack = []
        elif action == "FINISH":
            pass
        else:
            raise Exception("Invalid action: " + action)

    def add_node(self, node_id=None):
        n = Configuration.Node(len(self.nodes), node_id=node_id)
        self.nodes.append(n)
        print("    %s" % n)
        return n

    @property
    def passage(self):
        paragraphs = [' '.join(paragraph) for paragraph in self.tokens]
        passage = from_text(paragraphs, self.passage_id)
        terminals = passage.layer(layer0.LAYER_ID).all
        l1 = layer1.Layer1(passage)
        linkage = []
        for n in reversed(self.nodes):
            if all(t[0] == "L" for t in n.outgoing.values()):
                linkage.append(n)
                continue
            for child_index, tag in n.outgoing.items():
                child = self.nodes[child_index]
                child.node = self.add_layer1_node(child, child_index, l1, n, tag, terminals)
        for n in linkage:
            link_relation = [self.nodes[i].node for i, t in n.outgoing.items()
                             if t == layer1.EdgeTags.LinkRelation][0]
            link_args = (self.nodes[i].node for i, t in n.outgoing.items()
                         if t == layer1.EdgeTags.LinkArgument)
            n.node = l1.add_linkage(link_relation, link_args)
        return passage

    def add_layer1_node(self, child, child_index, l1, n, tag, terminals):
        if child.text:
            return n.node.add(layer1.EdgeTags.Terminal, terminals[child_index]).child
        if len(child.outgoing) == 1:
            grandchild_index = next(iter(child.outgoing))
            grandchild = self.nodes[grandchild_index]
            if grandchild.text:
                t = terminals[grandchild_index]
                if layer0.is_punct(t):
                    return l1.add_punct(n.node, t)
        return l1.add_fnode(n.node, tag)


class Parser:
    def __init__(self):
        self.config = None
        self.actions = [action + relation for action in ("NODE-", "EDGE-")
                        for name, relation in layer1.EdgeTags.__dict__.items()
                        if isinstance(relation, str) and not name.startswith('__')] +\
                       ["REDUCE", "SHIFT", "WRAP", "FINISH"]
        self.actions_reverse = {action: i for i, action in enumerate(self.actions)}
        self.features = [lambda config: len(config.stack),
                         lambda config: len(config.buffer)]
        self.weights = 0.01 * np.random.randn(len(self.actions), len(self.features))

    def train(self, passages, iterations=1):
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
                    if pred_action != true_action:
                        self.update(pred_action, true_action)
                    else:
                        correct += 1
                    # print("  predicted: %-15s true: %-15s stack: %-20s buffer: %-70s" %
                    print("  %-15s stack: %-40s buffer: %-70s" %
                          (true_action, self.config.stack, list(self.config.buffer)))
                    self.config.apply_action(true_action, node_id)
                    actions += 1
                    if true_action == "FINISH":
                        break
                print("  stack: %-40s buffer: %-70s" %
                      (self.config.stack, list(self.config.buffer)))
                out_f = "%s/%s%s.xml" % (args.outdir, args.prefix, passage.ID)
                sys.stderr.write("Writing passage '%s'...\n" % out_f)
                passage2file(self.config.passage, out_f)
                assert passage.equals(self.config.passage), "Oracle failed to produce true passage"
            print("Accuracy: %.3f (%d/%d)\n" % (correct/actions, correct, actions)
                  if actions else "No actions done")

    def parse(self, passages):
        print("%d passages to parse" % len(passages))
        for passage in passages:
            self.config = Configuration(passage, passage.ID)
            while True:
                action = self.predict_action()
                self.config.apply_action(action)
                if action == "FINISH":
                    break
            yield self.config.passage

    def predict_action(self):
        features = np.array([f(self.config) for f in self.features])
        return self.actions[np.argmax(self.weights.dot(features))]

    def update(self, pred_action, true_action):
        features = np.array([f(self.config) for f in self.features])
        self.weights[self.actions_reverse[true_action]] += features
        self.weights[self.actions_reverse[pred_action]] -= features


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
    for pred_passage in parser.parse(test_passages):
        outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
        sys.stderr.write("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile)
