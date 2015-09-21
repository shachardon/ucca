import argparse
import os
import time

import numpy as np
import sys

from action import Action
from state import State
from diff import diff_passages
from ucca import layer1
from scripts.util import file2passage
from oracle import Oracle
from util import passage2file

desc = """Transition-based parser for UCCA.
"""


class Parser:
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self):
        self.state = None  # State object created at each parse
        self.actions = [Action(action, tag) for action in
                        ("NODE", "LEFT-EDGE", "RIGHT-EDGE", "LEFT-REMOTE", "RIGHT-REMOTE", "ROOT", "IMPLICIT")
                        for name, tag in layer1.EdgeTags.__dict__.items()
                        if isinstance(tag, str) and not name.startswith('__')] +\
                       [Action(action) for action in
                        ("REDUCE", "SHIFT", "SWAP", "WRAP", "FINISH")]
        self.actions_reverse = {str(action): i for i, action in enumerate(self.actions)}
        self.features = [
            lambda: len(self.state.stack),
            lambda: len(self.state.buffer)
        ]
        self.weights = 0.01 * np.random.randn(len(self.actions), len(self.features))

    def feature_array(self):
        """
        Calculate features according to current configuration
        :return: NumPy array with all feature values
        """
        return np.array([f() for f in self.features])

    def train(self, passages, iterations=1, verbose=False, check_loops=True):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        """
        total_correct = 0
        total_actions = 0
        total_duration = 0
        print("Training %d iterations on %d passages" % (iterations, len(passages)))
        for iteration in range(1, iterations + 1):
            print("Iteration %d" % iteration)
            started = time.time()
            correct = 0
            actions = 0
            for passage in passages:
                print("passage " + passage.ID, end="\n" if verbose else ": ")
                self.state = State(passage, passage.ID, verbose=verbose)
                history = set()
                oracle = Oracle(passage)
                while True:
                    if check_loops:
                        h = hash(self.state)
                        assert h not in history, \
                            "Transition loop during training:\n%s\n%s" % (
                                self.state.str("\n"), oracle.str("\n"))
                        history.add(h)
                    # pred_action = self.predict_action()
                    true_action = oracle.get_action(self.state)
                    # if not self.update(pred_action, true_action):
                    #     correct += 1
                    if verbose:
                        # print("  predicted: %-15s true: %-15s stack: %-20s buffer: %-70s" %
                        print("  %-15s %s" % (true_action, self.state))
                    actions += 1
                    if not self.state.apply_action(true_action):
                        break  # action is FINISH
                if verbose:
                    print(" " * 18 + str(self.state))
                predicted = self.state.passage
                assert passage.equals(predicted),\
                    "Oracle failed to produce true passage\n" + diff_passages(passage, predicted)
            print("accuracy: %.3f (%d/%d)" % (correct/actions, correct, actions)
                  if actions else "No actions done", end="\n" if verbose else ", ")
            duration = time.time() - started
            print("duration: %0.3fms" % duration)
            total_correct += correct
            total_actions += actions
            total_duration += duration
            print()

        print("Trained %d iterations on %d passages" % (iterations, len(passages)))
        print("Overall accuracy: %.3f (%d/%d)" % (
            total_correct / total_actions, total_correct, total_actions))
        print("Total time: %.3fms (average time per passage: %.3fms)" % (
            total_duration, total_duration / len(passages)))

    def parse(self, passages, check_loops=True):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :return: generator of parsed passages
        """
        print("%d passages to parse" % len(passages))
        for passage in passages:
            self.state = State(passage, passage.ID)
            history = set()
            while self.state.apply_action(self.predict_action()):
                if check_loops:
                    h = hash(self.state)
                    assert h not in history,\
                        "Transition loop during parse:\n%s" % self.state.str("\n")
                    history.add(h)
            yield self.state.passage

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


def all_files(dirs):
    """
    :param dirs: a list of files and/or directories to look in
    :return: all files given, plus any files directly under any directory given
    """
    return [f for d in dirs or () for f in (os.listdir(d) if os.path.isdir(d) else (d,))]


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('train', nargs='+', help="passage file names to train on")
    argparser.add_argument('-t', '--test', nargs='+', help="passage file names to test on")
    argparser.add_argument('-o', '--outdir', default='.', help="output directory")
    argparser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
    args = argparser.parse_args()

    train_passages = [file2passage(filename) for filename in all_files(args.train)]
    test_passages = [file2passage(filename) for filename in all_files(args.test)]
    parser = Parser()
    parser.train(train_passages, check_loops=False)
    for pred_passage in parser.parse(test_passages):
        outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
        sys.stderr.write("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile)
