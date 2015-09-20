import argparse
import time
import sys

import numpy as np

from action import Action
from config import Configuration
from diff import diff_passages
from ucca import layer1
from scripts.util import file2passage, passage2file
from oracle import Oracle

desc = """Transition-based parser for UCCA.
"""


class Parser:
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self):
        self.config = None  # Configuration object created at each parse
        self.actions = [Action(action, tag) for action in
                        ("NODE", "LEFT-EDGE", "RIGHT-EDGE", "LEFT-REMOTE", "RIGHT-REMOTE", "ROOT", "IMPLICIT")
                        for name, tag in layer1.EdgeTags.__dict__.items()
                        if isinstance(tag, str) and not name.startswith('__')] +\
                       [Action(action) for action in
                        ("REDUCE", "SHIFT", "SWAP", "WRAP", "FINISH")]
        self.actions_reverse = {str(action): i for i, action in enumerate(self.actions)}
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

    def train(self, passages, iterations=1, check_loops=True):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        """
        print("%d training passages" % len(passages))
        for iteration in range(iterations):
            print("Iteration %d" % iteration)
            started = time.time()
            correct = 0
            actions = 0
            for passage in passages:
                self.config = Configuration(passage, passage.ID)
                history = set()
                oracle = Oracle(passage)
                while True:
                    if check_loops:
                        h = hash(self.config)
                        assert h not in history, \
                            "Transition loop during training:\n%s\n%s" % (
                                self.config.str("\n"), oracle.str("\n"))
                        history.add(h)
                    # pred_action = self.predict_action()
                    true_action = oracle.get_action(self.config)
                    # if not self.update(pred_action, true_action):
                    #     correct += 1
                    # print("  predicted: %-15s true: %-15s stack: %-20s buffer: %-70s" %
                    print("  %-15s %s" % (true_action, self.config))
                    actions += 1
                    if not self.config.apply_action(true_action):
                        break
                print(" " * 18 + str(self.config))
                out_f = "%s/%s%s.xml" % (args.outdir, args.prefix, passage.ID)
                sys.stderr.write("Writing passage '%s'...\n" % out_f)
                pred_passage = self.config.passage
                passage2file(pred_passage, out_f)
                assert passage.equals(pred_passage), "Oracle failed to produce true passage\n" + \
                                                     diff_passages(passage, pred_passage)
            print("Accuracy: %.3f (%d/%d)" % (correct/actions, correct, actions)
                  if actions else "No actions done")
            print("Duration: %0.3fms" % (time.time() - started))

    def parse(self, passages, check_loops=True):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :return: generator of parsed passages
        """
        print("%d passages to parse" % len(passages))
        for passage in passages:
            self.config = Configuration(passage, passage.ID)
            history = set()
            while self.config.apply_action(self.predict_action()):
                if check_loops:
                    h = hash(self.config)
                    assert h not in history,\
                        "Transition loop during parse:\n%s" % self.config.str("\n")
                    history.add(h)
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
        self.weights[self.actions_reverse[str(true_action)]] += features
        self.weights[self.actions_reverse[str(pred_action)]] -= features
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
    parser.train(train_passages, check_loops=False)
    # for pred_passage in parser.parse(test_passages):
    #     outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
    #     sys.stderr.write("Writing passage '%s'...\n" % outfile)
    #     passage2file(pred_passage, outfile)
