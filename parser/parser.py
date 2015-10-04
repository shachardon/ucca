import argparse
import os
import time

import numpy as np

from action import Action
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

    def train(self, passages, iterations=1, **kwargs):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        """
        print("Training %d iterations on %d passages" % (iterations, len(passages)))
        for iteration in range(1, iterations + 1):
            print("Iteration %d" % iteration, end=": ")
            self.parse(passages, train=True, **kwargs)

        print("Trained %d iterations on %d passages" % (iterations, len(passages)))

    def parse(self, passages, train=False, verbose=False, check_loops=True):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :param train: use oracle to train on given passages, or just parse with classifier?
        :param verbose: print long trace of performed actions?
        :param check_loops: check whether an infinite loop is reached (adds runtime overhead)?
        :return: generator of parsed passages
        """
        predicted_passages = []
        total_correct = 0
        total_actions = 0
        total_duration = 0
        end = "\n" if verbose else " "
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
            self.state = State(passage, passage.ID, verbose=verbose)
            history = set()
            if train:
                oracle = Oracle(passage)
            while True:
                if check_loops:
                    h = hash(self.state)
                    assert h not in history, "Transition loop:\n" + self.state.str("\n") +\
                                             "\n" + oracle.str("\n") if train else ""
                    history.add(h)
                if not train:  # FIXME remove this condition and uncomment code below
                    pred_action = self.predict_action()
                if train:
                    action = oracle.get_action(self.state)
                    # if not self.update(pred_action, action):
                    #     correct += 1
                else:
                    action = pred_action
                if verbose:
                    # print("  predicted: %-15s true: %-15s %s" % (pred_action, action, self.state)
                    print("  %-15s %s" % (action, self.state))
                actions += 1
                if not self.state.apply_action(action):
                    break  # action is FINISH
            if verbose:
                print(" " * 18 + str(self.state))
            predicted = self.state.passage
            if train:
                assert passage.equals(predicted),\
                    "Oracle failed to produce true passage\n" + diff_passages(passage, predicted)
                print("accuracy: %.3f (%d/%d)" % (correct/actions, correct, actions)
                      if actions else "No actions done", end=end)
            duration = time.time() - started
            print("time: %0.3fms" % duration)
            if verbose:
                print()
            predicted_passages.append(predicted)
            total_correct += correct
            total_actions += actions
            total_duration += duration

        if train and total_actions:
            print("Overall accuracy: %.3f (%d/%d)" % (
                total_correct / total_actions, total_correct, total_actions))
        if passages:
            print("Total time: %.3fms (average time per passage: %.3fms)" % (
                total_duration, total_duration / len(passages)))

        return predicted_passages

    def predict_action(self):
        """
        Choose action based on classifier
        :return: action with maximum probability according to classifier
        """
        # TODO do not predict an action that is illegal in the current state
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
    args = argparser.parse_args()

    parser = Parser()
    parser.train(all_files(args.train), check_loops=False)
    for pred_passage in parser.parse(all_files(args.test)):
        outfile = "%s/%s%s.xml" % (args.outdir, args.prefix, pred_passage.ID)
        print("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile)
