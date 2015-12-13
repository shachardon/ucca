import os
import random
import time
from itertools import groupby
from random import shuffle
from xml.etree.ElementTree import ParseError

from nltk import pos_tag

from action import Action
from averaged_perceptron import AveragedPerceptron
from config import Config
from features import FeatureExtractor
from oracle import Oracle
from state import State
from ucca import core, layer0
from ucca.evaluation import evaluate, print_aggregate, average_f1
from ucca.ioutil import file2passage, passage2file
from ucca.diffutil import diff_passages


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

    def train(self, passages, dev=None, iterations=1):
        """
        Train parser on given passages
        :param passages: iterable of Passage objects to train on
        :param dev: iterable of Passage objects to tune on
        :param iterations: number of iterations to perform
        :return: trained model
        """
        if not passages:
            if self.model_file is not None:  # Nothing to train on; pre-trained model given
                self.model.load(self.model_file)
            return self.model

        print("Training %d iterations" % iterations)
        for iteration in range(1, iterations + 1):
            print("Iteration %d: " % iteration)
            passages = [(passage, passage.ID) for _, passage in
                        self.parse(passages, mode="train")]
            shuffle(passages)
            if dev:
                print("Evaluating on dev passages")
                dev, scores = zip(*[((passage, passage.ID),
                                     evaluate(predicted_passage, passage,
                                              verbose=False, units=False, errors=False))
                                    for predicted_passage, passage in
                                    self.parse(dev, mode="dev")])
                score = average_f1(scores)
                print("Average F1 score on dev: %.3f" % score)
            print()
        self.model.average_weights()
        print("Trained %d iterations" % iterations)

        if self.model_file is not None:  # Save trained model
            self.model.save(self.model_file)
        print()

        return self.model

    def parse(self, passages, mode="test"):
        """
        Parse given passages
        :param passages: iterable of pairs of (either Passage objects, or of lists of lists of tokens),
                                               and passage IDs
        :param mode: "train", "test" or "dev".
                     If "train", use oracle to train on given passages.
                     Otherwise, just parse with classifier.
        :return: generator of pairs of (parsed passage, original passage)
        """
        train = (mode == "train")
        assert train or mode in ("test", "dev"), "Invalid parse mode: %s" % mode
        self.total_actions = 0
        self.total_correct = 0
        total_duration = 0
        total_words = 0
        num_passages = 0
        for passage, passage_id in passages:
            print("passage " + passage_id, end=Config().line_end, flush=True)
            started = time.time()
            self.action_count = 0
            self.correct_count = 0
            assert not train or isinstance(passage, core.Passage), "Cannot train on unannotated passage"
            self.state = State(passage, passage_id, callback=self.pos_tag)
            history = set()
            self.oracle = Oracle(passage) if isinstance(passage, core.Passage) else None
            try:
                self.parse_passage(history, train)  # This is where the actual parsing takes place
            except AssertionError as e:
                if train:
                    raise
                if Config().verbose:
                    print(e)
                print("failed, ", end="")
            if not train or Config().verify:
                predicted_passage = self.state.create_passage(assert_proper=Config().verify)
            else:
                predicted_passage = passages
            if self.oracle:  # passage is a Passage object
                if Config().verify:
                    self.verify_passage(passage, predicted_passage, train)
                print("accuracy: %.3f (%d/%d)" %
                      (self.correct_count/self.action_count, self.correct_count, self.action_count)
                      if self.action_count else "No actions done", end=Config().line_end)
            duration = time.time() - started
            words = len(passage.layer(layer0.LAYER_ID).all) if self.oracle else sum(map(len, passage))
            print("time: %0.3fs (%d words/second)" % (duration, words / duration),
                  end=Config().line_end + "\n", flush=True)
            self.total_correct += self.correct_count
            self.total_actions += self.action_count
            total_duration += duration
            total_words += words
            num_passages += 1
            yield predicted_passage, passage

        if num_passages > 1:
            print("Parsed %d passages" % num_passages)
            if self.oracle and self.total_actions:
                print("Overall %s accuracy: %.3f (%d/%d)" %
                      (mode,
                       self.total_correct / self.total_actions, self.total_correct, self.total_actions))
            print("Total time: %.3fs (average time/passage: %.3fs, average words/second: %d)" % (
                total_duration, total_duration / num_passages, total_words / total_duration),
                  flush=True)

    @staticmethod
    def read_passage(passage):
        """
        Read a passage given in any format
        :param passage: either a core.Passage, a file, or a list of list of strings (paragraphs, words)
        :return: a core.Passage and its ID if given a Passage or file, or else the given list of lists
        """
        if isinstance(passage, core.Passage):
            passage_id = passage.ID
        elif os.path.exists(passage):  # a file
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

            true_action = None
            if self.oracle is not None:
                try:
                    true_action = self.oracle.get_action(self.state)
                    self.state.assert_valid(true_action)
                except AttributeError as e:
                    if train:
                        raise Exception("Error in oracle during training") from e
                except AssertionError as e:
                    if Config().verbose:
                        print("Oracle returned invalid action: %s" % true_action)
                        print(e)
                        true_action = None

            features = self.feature_extractor.extract_features(self.state)
            predicted_action = self.predict_action(features, true_action)
            action = predicted_action
            prefix = " "  # Will be "*" if true action is taken instead of predicted one
            if true_action is None:
                true_action = "?"
            elif predicted_action == true_action:
                self.correct_count += 1
            elif train:
                self.model.update(features, predicted_action, true_action, Config().learning_rate)
                if random.random() < Config().override_action_probability:
                    action = true_action
                    prefix = "*"
            self.action_count += 1
            self.state.transition(action)
            if Config().verbose:
                if self.oracle is None:
                    print("%s action: %-15s %s" % (prefix, predicted_action, self.state))
                else:
                    print("%s predicted: %-15s true: %-15s %s" % (
                        prefix, predicted_action, true_action, self.state))
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

    def predict_action(self, features, true_action=None):
        """
        Choose action based on classifier
        :param features: extracted feature values
        :param true_action: from the oracle, to copy orig_node if the same action is selected
        :return: valid action with maximum probability according to classifier
        """
        scores = self.model.score(features)
        best_action = self.select_action(scores.argmax(), true_action)
        if self.state.is_valid(best_action):
            return best_action
        scores_sorted = scores.argsort()[-2::-1]  # Exclude max, already checked
        actions = (self.select_action(i, true_action) for i in scores_sorted)
        try:
            return next(action for action in actions if self.state.is_valid(action))
        except StopIteration as e:
            raise Exception("No valid actions available") from e

    @staticmethod
    def select_action(i, true_action):
        action = Action.by_id(i)
        return true_action if true_action is not None and action == true_action else action

    @staticmethod
    def verify_passage(passage, predicted_passage, show_diff):
        """
        Compare predicted passage to true passage and die if they differ
        :param passage: true passage
        :param predicted_passage: predicted passage to compare
        :param show_diff: if passages differ, show the difference between them?
                          Depends on predicted_passage having the original node IDs annotated
                          in the "remarks" field for each node.
        """
        assert passage.equals(predicted_passage), "Failed to produce true passage" + \
                                                  (diff_passages(
                                                      passage, predicted_passage) if show_diff else "")

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


def read_passages(passages):
    files = all_files(passages)
    return (Parser.read_passage(passage) for passage in files) if files else []


def write_passage(passage, outdir, prefix, binary, verbose):
    suffix = ".pickle" if binary else ".xml"
    outfile = outdir + os.path.sep + prefix + passage.ID + suffix
    if verbose:
        print("Writing passage '%s'..." % outfile)
    passage2file(passage, outfile, binary=binary)


def main():
    args = Config().args
    parser = Parser(args.model)
    parser.train(read_passages(args.train), dev=read_passages(args.dev), iterations=args.iterations)
    if args.passages:
        if args.train:
            print("Evaluating on test passages")
        scores = []
        for guessed_passage, ref_passage in parser.parse(read_passages(args.passages)):
            if isinstance(ref_passage, core.Passage):
                scores.append(evaluate(guessed_passage, ref_passage,
                                       verbose=args.verbose and guessed_passage is not None))
            if guessed_passage is not None:
                write_passage(guessed_passage, args.outdir, args.prefix, args.binary, args.verbose)
        if scores:
            print()
            print("Average F1 score on test: %.3f" % average_f1(scores))
            print("Aggregated scores:")
            print()
            print_aggregate(scores)


if __name__ == "__main__":
    main()
