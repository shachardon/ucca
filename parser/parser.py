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
import oracle


class Configuration:
    def __init__(self, passage, passage_id):
        if isinstance(passage, Passage):
            terminals = [x.ID for x in passage.layer(layer0.LAYER_ID).all]
            tokens = [[x.text for x in xs]
                      for _, xs in groupby(passage.layer(layer0.LAYER_ID).all,
                                           key=attrgetter('paragraph'))]
        else:
            tokens = [token for paragraph in passage for token in paragraph]
            terminals = ["0.%d" % (i+1) for i in enumerate(tokens)]
        paragraphs = [' '.join(paragraph) for paragraph in tokens]
        self.stack = []
        self.buffer = deque(terminals)
        self.passage = from_text(paragraphs, passage_id)

    def is_terminal(self):
        return not self.buffer

    def apply_action(self, action):
        m = re.match("LEFT-ARC-(.*)", action)
        if m:
            return self.apply_left_arc(m.group(0))
        m = re.match("RIGHT-ARC-(.*)", action)
        if m:
            return self.apply_right_arc(m.group(0))
        if action == "REDUCE":
            return self.apply_reduce()
        if action == "SHIFT":
            return self.apply_shift()
        raise Exception("Invalid action: " + action)

    def apply_left_arc(self, tag):
        return self.add_edge(self.buffer[0], self.stack.pop(), tag)

    def apply_right_arc(self, tag):
        b = self.buffer[0]
        edge = self.add_edge(self.stack[-1], b, tag)
        self.stack.append(b)
        return edge

    def apply_reduce(self):
        return self.stack.pop()

    def apply_shift(self):
        return self.stack.append(self.buffer.popleft())

    def add_edge(self, i, j, tag):
        return self.passage.by_id(i).add(tag, self.passage.by_id(j))


class Parser:
    def __init__(self):
        self.config = None
        self.actions = [action + relation for action in ("LEFT-ARC-", "RIGHT-ARC-")
                        for relation in layer1.EdgeTags.__dict__.values()
                        if isinstance(relation, str)] + ["REDUCE", "SHIFT"]
        self.actions_reverse = {action: i for i, action in enumerate(self.actions)}
        self.features = [lambda config: len(config.stack),
                         lambda config: len(config.buffer)]
        self.weights = np.zeros((len(self.actions), len(self.features)))

    def train(self, passages, iterations=1):
        print("%d training passages" % len(passages))
        for iteration in range(iterations):
            print("Iteration %d" % iteration)
            correct = 0
            actions = 0
            for passage in passages:
                self.config = Configuration(passage, passage.ID)
                while not self.config.is_terminal():
                    pred_action = self.predict_action()
                    true_action = oracle.get_action(passage, self.config)
                    if pred_action != true_action:
                        self.update(pred_action, true_action)
                    else:
                        correct += 1
                    self.config.apply_action(true_action)
                    actions += 1
                    print("  pred: %-20s true: %s" % (pred_action, true_action))
            print("Accuracy: %.3f (%d/%d)\n" % (correct/actions, correct, actions)
                  if actions else "No actions done")

    def parse(self, passages):
        print("%d passages to parse" % len(passages))
        for passage in passages:
            self.config = Configuration(passage, passage.ID)
            while not self.config.is_terminal():
                self.config.apply_action(self.predict_action())
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
