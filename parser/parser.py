import os
import random
import time
from itertools import groupby
from random import shuffle
from xml.etree.ElementTree import ParseError

from nltk import pos_tag

from action import Action, NODE, IMPLICIT
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

        self.model = AveragedPerceptron(len(Action.get_all_actions()))
        self.model_file = model_file
        self.feature_extractor = FeatureExtractor()

    def train(self, passages, iterations=1):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param iterations: number of iterations to perform
        :return: trained model
        """
        if not passages:
            if self.model_file is not None:  # Nothing to train on; pre-trained model given
                if not Config().quiet:
                    print("Loading model from '%s'... " % self.model_file, end="")
                started = time.time()
                self.model.load(self.model_file)
                if not Config().quiet:
                    print("Done (%.3fs)." % (time.time() - started))
            return

        if not Config().quiet:
            print("Training %d iterations on %d passages" % (iterations, len(passages)))
        for iteration in range(1, iterations + 1):
            if not Config().quiet:
                print("Iteration %d" % iteration, end=": ")
            shuffle(passages)
            all(self.parse(passages, train=True))
        self.model.average_weights()
        if not Config().quiet:
            print("Trained %d iterations on %d passages" % (iterations, len(passages)))

        if self.model_file is not None:  # Save trained model
            if not Config().quiet:
                print("Saving model to '%s'... " % self.model_file, end="")
            started = time.time()
            self.model.save(self.model_file)
            if not Config().quiet:
                print("Done (%.3fs)." % (time.time() - started))

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
        if not Config().quiet:
            print((str(len(passages)) if passages else "No") + " passages to parse")
        for passage in passages:
            started = time.time()
            self.action_count = 0
            self.correct_count = 0
            passage, passage_id = self.read_passage(passage)
            assert not train or isinstance(passage, core.Passage), "Cannot train on unannotated passage"
            self.state = State(passage, passage_id, self.pos_tag)
            history = set()
            self.oracle = Oracle(passage) if isinstance(passage, core.Passage) else None
            self.parse_passage(history, train)  # This is where the actual parsing takes place
            predicted_passage = self.state.create_passage() if not train or Config().verify else passage
            if self.oracle:  # passage is a Passage object
                if Config().verify:
                    self.verify_passage(passage, predicted_passage)
                if not Config().quiet:
                    print("accuracy: %.3f (%d/%d)" %
                          (self.correct_count/self.action_count, self.correct_count, self.action_count)
                          if self.action_count else "No actions done", end=Config().line_end)
            duration = time.time() - started
            words = len(passage.layer(layer0.LAYER_ID).all) if self.oracle else sum(map(len, passage))
            if not Config().quiet:
                print("time: %0.3fs (%d words/second)" % (duration, words / duration),
                      end=Config().line_end + "\n", flush=True)
            self.total_correct += self.correct_count
            self.total_actions += self.action_count
            total_duration += duration
            total_words += words
            yield predicted_passage

        if not Config().quiet and self.oracle and self.total_actions:
            print("Overall %s accuracy: %.3f (%d/%d)" % (
                "train" if train else "test",
                self.total_correct / self.total_actions, self.total_correct, self.total_actions))
        if not Config().quiet and passages:
            print("Total time: %.3fs (average time/passage: %.3fs, average words/second: %d)" % (
                total_duration, total_duration / len(passages), total_words / total_duration),
                  flush=True)

    @staticmethod
    def read_passage(passage):
        """
        Read a passage given in any format
        :param passage: either a core.Passage, a file, or a list of list of strings (paragraphs, words)
        :return: a core.Passage and its ID if given a Passage or file, or else the given list of lists
        """
        if isinstance(passage, core.Passage):
            if not Config().quiet:
                print("passage " + passage.ID, end=Config().line_end)
            passage_id = passage.ID
        elif os.path.exists(passage):  # a file
            if not Config().quiet:
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
        else:
            raise IOError("File not found: %s" % passage)
        return passage, passage_id

    def parse_passage(self, history=None, train=False):
        """
        Internal method to parse a single passage
        :param history: set of hashed states in the parser's history, if loop checking is enabled
        :param train: use oracle to train on given passages, or just parse with classifier?
        """
        if Config().verbose:
            print("  initial state: %s" % self.state)
        while True:
            if Config().check_loops and history is not None:
                self.check_loop(history, train)
            features = self.feature_extractor.extract_features(self.state)
            action = self.predict_action(features)
            prefix = ""  # Will be "*" if true action is taken instead of predicted one
            if self.oracle:
                try:
                    true_action = self.oracle.get_action(self.state)
                    assert self.state.is_valid(action), "Oracle returned invalid action: %s" % action
                except AttributeError as e:
                    if train:
                        raise Exception("Error in oracle during training") from e
                    else:
                        true_action = None
                if true_action is None:
                    true_action = "?"
                elif action == true_action:
                    self.correct_count += 1
                    action = true_action  # to copy orig_node
                elif train:
                    self.model.update(features, action, true_action)
                    if action.is_type(NODE, IMPLICIT) or (
                                random.random() < Config().override_action_probability):
                        action = true_action
                        prefix = "*"
            self.action_count += 1
            self.state.transition(action)
            if Config().verbose:
                if self.oracle:
                    print(" %s predicted: %-15s true: %-15s %s" % (prefix, action, true_action, self.state))
                else:
                    print(" %s action: %-15s %s" % (prefix, action, self.state))
                for line in self.state.log:
                    print("    " + line)
            if self.state.finished:
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
        :param predicted_passage: predicted passage to compare
        """
        assert passage.equals(predicted_passage), \
            "Failed to produce true passage\n" + diff_passages(
                passage, predicted_passage)

    @staticmethod
    def pos_tag(state):
        """
        Function to pass to State to POS tag the tokens when created
        :param state: State object to modify
        """
        tokens = [token for tokens in state.tokens for token in tokens]
        tokens, tags = zip(*pos_tag(tokens))
        if Config().verbose:
            print(" ".join("%s/%s" % (token, tag) for (token, tag) in zip(tokens, tags)))
        for node, tag in zip(state.nodes, tags):
            node.pos_tag = tag


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
    parser.train(all_files(args.train), iterations=args.iterations)
    for pred_passage in parser.parse(all_files(args.passages)):
        suffix = ".pickle" if args.binary else ".xml"
        outfile = args.outdir + os.path.sep + args.prefix + pred_passage.ID + suffix
        if args.verbose:
            print("Writing passage '%s'..." % outfile)
        passage2file(pred_passage, outfile, binary=args.binary)
