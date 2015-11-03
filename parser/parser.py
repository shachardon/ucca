import os
import time
from itertools import groupby
from sys import stdout, stderr
from xml.etree.ElementTree import ParseError

import numpy as np

from action import NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE, REDUCE, SHIFT, SWAP, FINISH
from classifier import Classifier
from config import Config
from diff import diff_passages
from oracle import Oracle
from scripts.util import file2passage, passage2file
from state import State
from ucca import core, layer0, layer1


class Parser(object):
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self):
        self.state = None  # State object created at each parse
        self.oracle = None  # Oracle object created at each parse
        self.action_count = 0
        self.correct_count = 0
        self.total_actions = 0
        self.total_correct = 0

        actions = [action(tag) for action in
                        (NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE)
                   for name, tag in layer1.EdgeTags.__dict__.items()
                   if isinstance(tag, str) and not name.startswith('__')] + \
                  [REDUCE, SHIFT, FINISH]
        if Config().compound_swap:
            actions.extend(SWAP(i) for i in range(1, Config().max_swap + 1))
        else:
            actions.append(SWAP)

        self.classifier = Classifier(actions)

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
        self.total_actions = 0
        self.total_correct = 0
        total_duration = 0
        total_words = 0
        print((str(len(passages)) if passages else "No") + " passages to parse")
        for passage in passages:
            started = time.time()
            self.action_count = 0
            self.correct_count = 0
            passage, passage_id = self.read_passage(passage)
            self.state = State(passage, passage_id)
            history = set()
            if train:
                self.oracle = Oracle(passage)
            self.parse_passage(history, train)
            if Config().verbose:
                print(" " * 18 + str(self.state))
            if train:
                if Config().verify:
                    self.verify_passage(passage)
                print("accuracy: %.3f (%d/%d)" %
                      (self.correct_count/self.action_count, self.correct_count, self.action_count)
                      if self.action_count else "No actions done", end=Config().line_end)
            else:
                predicted_passages.append(self.state.create_passage())
            duration = time.time() - started
            words = len(passage.layer(layer0.LAYER_ID).all)
            print("time: %0.3fs (%d words/second)" % (duration, words / duration),
                  end=Config().line_end + "\n")
            self.total_correct += self.correct_count
            self.total_actions += self.action_count
            total_duration += duration
            total_words + words

        if train and self.total_actions:
            print("Overall accuracy: %.3f (%d/%d)" % (
                self.total_correct / self.total_actions, self.total_correct, self.total_actions))
        if passages:
            print("Total time: %.3fs (average time/passage: %.3fs, average words/second: %d)" % (
                total_duration, total_duration / len(passages), total_words / total_duration))

        return predicted_passages

    @staticmethod
    def read_passage(passage):
        if isinstance(passage, core.Passage):
            print("passage " + passage.ID, end=Config().line_end)
            passage_id = passage.ID
        elif os.path.exists(passage):  # a file
            print("passage '%s'" % passage, end=Config().line_end)
            try:
                passage = file2passage(passage)  # XML or binary format
                passage_id = passage.ID
            except (IOError, ParseError):
                passage_id = os.path.basename(passage)
                with open(passage) as text_file:  # simple text file
                    lines = (line.strip() for line in text_file.readlines())
                    passage = [[token for line in group for token in line.split()]
                               for is_sep, group in groupby(lines, lambda x: not x)
                               if not is_sep]
        else:  # Assume it is a list of list of strings (or the like)
            passage_id = None
        return passage, passage_id

    def parse_passage(self, history=None, train=False):
        """
        Internal method to parse a single passage
        :param history: set of hashes states in the parser's history
        :param train: use oracle to train on given passages, or just parse with classifier?
        """
        while True:
            if Config().check_loops and history is not None:
                h = hash(self.state)
                assert h not in history, "Transition loop:\n" + self.state.str("\n") + \
                                         "\n" + self.oracle.str("\n") if train else ""
                history.add(h)
            self.classifier.calc_features(self.state)
            predicted_action = self.classifier.predict_action(self.state)
            if train:
                true_action = self.oracle.get_action(self.state)
                if not self.classifier.update(predicted_action, true_action):
                    self.correct_count += 1
                if Config().verbose:
                    print("  predicted: %-15s true: %-15s %s" % (
                        predicted_action, true_action, self.state))
            else:
                true_action = predicted_action
                if Config().verbose:
                    print("  action: %-15s %s" % (predicted_action, self.state))
            self.action_count += 1
            if not self.state.apply_action(true_action):
                return  # action is FINISH

    def verify_passage(self, passage):
        """
        Compare predicted passage to true passage and die if they differ
        :param passage: true passage
        """
        predicted_passage = self.state.create_passage()
        assert passage.equals(predicted_passage), \
            "Oracle failed to produce true passage\n" + diff_passages(
                passage, predicted_passage)


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
    if args.seed:
        np.random.seed(int(args.seed))
    parser = Parser()
    parser.train(all_files(args.train))
    stdout.flush()
    stderr.flush()
    for pred_passage in parser.parse(all_files(args.test)):
        suffix = ".pickle" if args.binary else ".xml"
        outfile = args.outdir + os.path.sep + args.prefix + pred_passage.ID + suffix
        print("Writing passage '%s'...\n" % outfile)
        passage2file(pred_passage, outfile, binary=args.binary)
