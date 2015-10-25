import argparse
import os
import time

import numpy as np

from action import NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE, REDUCE, SHIFT, SWAP, FINISH
from config import parse_args, VERBOSE, CHECK_LOOPS
from state import State
from diff import diff_passages
from oracle import Oracle
from ucca import core, layer1
from scripts.util import file2passage, passage2file

desc = """Transition-based parser for UCCA.
"""


class Parser:
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self):
        self.state = None  # State object created at each parse
        self.actions = [action(tag) for action in
                        (NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE)
                        for name, tag in layer1.EdgeTags.__dict__.items()
                        if isinstance(tag, str) and not name.startswith('__')] +\
                       [REDUCE, SHIFT, SWAP, FINISH]
        self.actions_reverse = {str(action): i for i, action in enumerate(self.actions)}
        self.features = [
            lambda: len(self.state.stack),
            lambda: len(self.state.buffer)
        ]
        self.weights = 0.01 * np.random.randn(len(self.actions), len(self.features))

    def calc_features(self):
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
        print("Training %d iterations on %d passages" % (iterations, len(passages)))
        for iteration in range(1, iterations + 1):
            print("Iteration %d" % iteration, end=": ")
            self.parse(passages, train=True)

        print("Trained %d iterations on %d passages" % (iterations, len(passages)))

    def parse(self, passages, train=False):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :param train: use oracle to train on given passages, or just parse with classifier?
        :return: generator of parsed passages
        """
        predicted_passages = []
        total_correct = 0
        total_actions = 0
        total_duration = 0
        end = "\n" if VERBOSE else " "
        print((str(len(passages)) if passages else "No") + " passages to parse")
        for passage in passages:
            started = time.time()
            correct = 0
            actions = 0
            if isinstance(passage, core.Passage):
                print("passage " + passage.ID, end=end)
            else:
                print("passage '%s'" % passage, end=end)
                passage = file2passage(passage)
            # TODO handle passage given as text, pass to State as list of lists of strings
            self.state = State(passage, passage.ID)
            history = set()
            if train:
                oracle = Oracle(passage)
            while True:
                if CHECK_LOOPS:
                    h = hash(self.state)
                    assert h not in history, "Transition loop:\n" + self.state.str("\n") +\
                                             "\n" + oracle.str("\n") if train else ""
                    history.add(h)
                pred_action = self.predict_action()
                if train:
                    action = oracle.get_action(self.state)
                    if not self.update(pred_action, action):
                        correct += 1
                else:
                    action = pred_action
                if VERBOSE:
                    # print("  predicted: %-15s true: %-15s %s" % (pred_action, action, self.state)
                    print("  %-15s %s" % (action, self.state))
                actions += 1
                if not self.state.apply_action(action):
                    break  # action is FINISH
            if VERBOSE:
                print(" " * 18 + str(self.state))
            predicted = self.state.passage
            if train:
                assert passage.equals(predicted),\
                    "Oracle failed to produce true passage\n" + diff_passages(passage, predicted)
                print("accuracy: %.3f (%d/%d)" % (correct/actions, correct, actions)
                      if actions else "No actions done", end=end)
            duration = time.time() - started
            print("time: %0.3fs" % duration)
            if VERBOSE:
                print()
            predicted_passages.append(predicted)
            total_correct += correct
            total_actions += actions
            total_duration += duration

        if train and total_actions:
            print("Overall accuracy: %.3f (%d/%d)" % (
                total_correct / total_actions, total_correct, total_actions))
        if passages:
            print("Total time: %.3fs (average time per passage: %.3fs)" % (
                total_duration, total_duration / len(passages)))

        return predicted_passages

    def predict_action(self):
        """
        Choose action based on classifier
        :return: action with maximum probability according to classifier
        """
        # TODO do not predict an action that is illegal in the current state
        features = self.calc_features()
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
        features = self.calc_features()
        self.weights[self.actions_reverse[str(true_action)]] += features
        self.weights[self.actions_reverse[str(pred_action)]] -= features
        return True


def all_files(dirs):
    """
    :param dirs: a list of files and/or directories to look in
    :return: all files given, plus any files directly under any directory given
    """
    if not dirs:
        return ()
    dirs += [os.path.join(d, f) for d in dirs if os.path.isdir(d) for f in os.listdir(d)]
    return [f for f in dirs if not os.path.isdir(f)]


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('train', nargs='+', help="passage file names to train on")
    argparser.add_argument('-t', '--test', nargs='+', help="passage file names to test on")
    argparser.add_argument('-o', '--outdir', default='.', help="output directory")
    argparser.add_argument('-p', '--prefix', default='ucca_passage', help="output filename prefix")
    args = parse_args(argparser)

    parser = Parser()
    parser.train(all_files(args.train))
    for pred_passage in parser.parse(all_files(args.test)):
        outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
        print("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile)
