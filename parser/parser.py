import os
from random import shuffle
from xml.etree.ElementTree import ParseError

import time
from itertools import groupby
from sys import stdout, stderr

from action import Action
from averaged_perceptron import AveragedPerceptron
from config import Config
from diff import diff_passages
from features import FeatureExtractor
from oracle import Oracle
from scripts.util import file2passage, passage2file
from state import State
from ucca import core, layer0


class Parser(object):
    """
    Main class to implement transition-based UCCA parser
    """
    def __init__(self, model_file=None):
        self.state = None  # State object created at each parse
        self.oracle = None  # Oracle object created at each parse
        self.action_count = 0
        self.correct_count = 0
        self.total_actions = 0
        self.total_correct = 0

        self.feature_extractor = FeatureExtractor()
        self.model = AveragedPerceptron(len(Action.get_all_actions()))
        self.model_file = model_file

    def train(self, passages, iterations=1):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        :return: trained model
        """
        if not passages:
            if self.model_file is not None:  # Nothing to train on; pre-trained model given
                self.model.load(self.model_file)
            return

        print("Training %d iterations on %d passages" % (iterations, len(passages)))
        for iteration in range(1, iterations + 1):
            print("Iteration %d" % iteration, end=": ")
            all(self.parse(passages, train=True))
            shuffle(passages)
        self.model.average_weights()
        print("Trained %d iterations on %d passages" % (iterations, len(passages)))

        if self.model_file is not None:  # Save trained model
            self.model.save(self.model_file)
            print("Saved model to '%s'" % self.model_file)

        return self.model

    def parse(self, passages, train=False):
        """
        Parse given passages
        :param passages: iterable of either Passage objects, or of lists of lists of tokens
        :param train: use oracle to train on given passages, or just parse with classifier?
        :return: generator of parsed passages
        """
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
            self.oracle = Oracle(passage) if isinstance(passage, core.Passage) else None
            self.parse_passage(history, train)  # This is where the actual parsing takes place
            predicted_passage = self.state.create_passage() if not train or Config().verify else passage
            if Config().verbose:
                print(" " * 18 + str(self.state))
            if self.oracle:  # passage is a Passage object
                if Config().verify:
                    self.verify_passage(passage, predicted_passage)
                print("accuracy: %.3f (%d/%d)" %
                      (self.correct_count/self.action_count, self.correct_count, self.action_count)
                      if self.action_count else "No actions done", end=Config().line_end)
            duration = time.time() - started
            words = len(passage.layer(layer0.LAYER_ID).all) if self.oracle else sum(map(len, passage))
            print("time: %0.3fs (%d words/second)" % (duration, words / duration),
                  end=Config().line_end)
            self.total_correct += self.correct_count
            self.total_actions += self.action_count
            total_duration += duration
            total_words += words
            yield predicted_passage

        if self.oracle and self.total_actions:
            print("Overall %s accuracy: %.3f (%d/%d)" % (
                "train" if train else "test",
                self.total_correct / self.total_actions, self.total_correct, self.total_actions))
        if passages:
            print("Total time: %.3fs (average time/passage: %.3fs, average words/second: %d)" % (
                total_duration, total_duration / len(passages), total_words / total_duration))

        stdout.flush()
        stderr.flush()

    @staticmethod
    def read_passage(passage):
        """
        Read a passage given in any format
        :param passage: either a core.Passage, a file, or a list of list of strings (paragraphs, words)
        :return: a core.Passage and its ID if given a Passage or file, or else the given list of lists
        """
        if isinstance(passage, core.Passage):
            print("passage " + passage.ID, end=Config().line_end)
            passage_id = passage.ID
        elif os.path.exists(passage):  # a file
            print("passage '%s'" % passage, end=Config().line_end)
            try:
                passage = file2passage(passage)  # XML or binary format
                passage_id = passage.ID
            except (IOError, ParseError):
                passage_id = os.path.splitext(os.path.basename(passage))[0]
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
        :param history: set of hashed states in the parser's history, if loop checking is enabled
        :param train: use oracle to train on given passages, or just parse with classifier?
        """
        while True:
            if Config().check_loops and history is not None:
                self.check_loop(history, train)
            features = self.feature_extractor.extract_features(self.state)
            action = self.predict_action(features)
            if self.oracle:
                true_action = self.oracle.get_action(self.state)
                if action == true_action:
                    self.correct_count += 1
                elif train:
                    self.model.update(features, action, true_action)
                if Config().verbose:
                    print("  predicted: %-15s true: %-15s %s" % (
                        action, true_action, self.state))
                action = true_action
            elif Config().verbose:
                print("  action: %-15s %s" % (action, self.state))
            self.action_count += 1
            if not self.state.transition(action):
                return  # action is FINISH

    def check_loop(self, history, train):
        """
        Check if the current state has already occurred, indicating a loop
        :param history: set of hashed states in the parser's history
        :param train: whether to print the oracle in case of an assertion error
        """
        h = hash(self.state)
        assert h not in history, "Transition loop:\n" + self.state.str("\n") + \
                                 "\n" + self.oracle.str("\n") if train else ""
        history.add(h)

    def predict_action(self, features):
        """
        Choose action based on classifier
        :param features: extracted feature values
        :return: valid action with maximum probability according to classifier
        """
        scores = self.model.score(features)
        best_action = Action.by_id(scores.argmax())
        if self.state.is_valid(best_action):
            return best_action
        actions = (Action.by_id(i) for i in scores.argsort()[-2::-1])  # Exclude max, already checked
        try:
            return next(action for action in actions if self.state.is_valid(action))
        except StopIteration as e:
            raise Exception("No valid actions available") from e

    @staticmethod
    def verify_passage(passage, predicted_passage):
        """
        Compare predicted passage to true passage and die if they differ
        :param passage: true passage
        """
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
    parser = Parser(args.model)
    parser.train(all_files(args.train))
    for pred_passage in parser.parse(all_files(args.passages)):
        suffix = ".pickle" if args.binary else ".xml"
        outfile = args.outdir + os.path.sep + args.prefix + pred_passage.ID + suffix
        print("Writing passage '%s'..." % outfile)
        passage2file(pred_passage, outfile, binary=args.binary)
