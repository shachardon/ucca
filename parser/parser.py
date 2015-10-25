from itertools import groupby
import os
from sys import stdout, stderr
import time
from xml.etree.ElementTree import ParseError

import numpy as np

from action import NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE, REDUCE, SHIFT, SWAP, FINISH
from config import Config
from state import State
from diff import diff_passages
from oracle import Oracle
from ucca import core, layer1
from scripts.util import file2passage, passage2file


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
        end = "\n" if Config.verbose else " "
        print((str(len(passages)) if passages else "No") + " passages to parse")
        for true_passage in passages:
            started = time.time()
            correct = 0
            actions = 0
            if isinstance(true_passage, core.Passage):
                print("passage " + true_passage.ID, end=end)
                passage_id = true_passage.ID
            elif os.path.exists(true_passage):  # a file
                print("passage '%s'" % true_passage, end=end)
                try:
                    true_passage = file2passage(true_passage)  # XML or binary format
                    passage_id = true_passage.ID
                except (IOError, ParseError):
                    passage_id = os.path.basename(true_passage)
                    with open(true_passage) as text_file:  # simple text file
                        lines = (line.strip() for line in text_file.readlines())
                        true_passage = [[token for line in group for token in line.split()]
                                        for is_sep, group in groupby(lines, lambda x: not x)
                                        if not is_sep]
            self.state = State(true_passage, passage_id)
            history = set()
            if train:
                oracle = Oracle(true_passage)
            while True:
                if Config.checkloops:
                    h = hash(self.state)
                    assert h not in history, "Transition loop:\n" + self.state.str("\n") +\
                                             "\n" + oracle.str("\n") if train else ""
                    history.add(h)
                predicted_action = self.predict_action()
                if train:
                    true_action = oracle.get_action(self.state)
                    if not self.update(predicted_action, true_action):
                        correct += 1
                    if Config.verbose:
                        print("  predicted: %-15s true: %-15s %s" % (
                            predicted_action, true_action, self.state))
                else:
                    true_action = predicted_action
                    if Config.verbose:
                        print("  action: %-15s %s" % (predicted_action, self.state))
                actions += 1
                if not self.state.apply_action(true_action):
                    break  # action is FINISH
            if Config.verbose:
                print(" " * 18 + str(self.state))
            predicted_passage = self.state.passage
            if train:
                assert true_passage.equals(predicted_passage),\
                    "Oracle failed to produce true passage\n" + diff_passages(
                        true_passage, predicted_passage)
                print("accuracy: %.3f (%d/%d)" % (correct/actions, correct, actions)
                      if actions else "No actions done", end=end)
            duration = time.time() - started
            print("time: %0.3fs" % duration)
            if Config.verbose:
                print()
            predicted_passages.append(predicted_passage)
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
    args = Config().args
    parser = Parser()
    parser.train(all_files(args.train))
    stdout.flush()
    stderr.flush()
    for pred_passage in parser.parse(all_files(args.test)):
        outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
        print("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile)
