import os
import shelve
import time
from collections import defaultdict

import numpy as np


class Weights(object):
    """
    The weights for one feature, for all labels
    """
    def __init__(self, num_labels, weights=None):
        self.num_labels = num_labels
        if weights is None:
            self.weights = 0.01 * np.random.randn(num_labels)
            self.update_count = 0
            self._last_update = np.zeros(num_labels, dtype=int)
            self._totals = np.zeros(num_labels, dtype=float)
        else:
            self.weights = weights

    def update(self, label, value, update_index):
        """
        Add a value to the entry of the given label
        :param label: label to index by
        :param value: value to add
        :param update_index: which update this is (for averaging)
        """
        self.update_count += 1
        n = update_index - self._last_update[label]
        self._totals[label] += n * self.weights[label]
        self.weights[label] += value
        self._last_update[label] = update_index

    def average(self, update_index):
        """
        Average weights over all updates
        :param update_index: number of updated to average over
        :return new Weights object with the weights averaged
        """
        n = update_index - self._last_update
        totals = self._totals + n * self.weights
        averaged_weights = totals / update_index
        return Weights(self.num_labels, averaged_weights)


class AveragedPerceptron(object):
    def __init__(self, num_labels, min_update=1, weights=None):
        self.num_labels = num_labels
        self.min_update = min_update
        self.weights = defaultdict(lambda: Weights(num_labels))
        self._update_index = 0
        self.is_frozen = False
        if weights is not None:
            self.weights.update(weights)

    def score(self, features):
        """
        Calculate score for each label
        :param features: extracted feature values, in the form of a dict (name -> value)
        :return: score for each label: dict (label -> score)
        """
        scores = np.zeros(self.num_labels)
        for feature, value in features.items():
            if not value:
                continue
            weights = self.weights.get(feature)
            if weights is None or not self.is_frozen and weights.update_count < self.min_update:
                continue
            scores += value * weights.weights
        return dict(enumerate(scores))

    def update(self, features, pred, true, learning_rate=1):
        """
        Update classifier weights according to predicted and true labels
        :param features: extracted feature values, in the form of a dict (name: value)
        :param pred: label predicted by the classifier (non-negative integer less than num_labels)
        :param true: true label (non-negative integer less than num_labels)
        :param learning_rate: how much to scale the feature vector for the weight update
        """
        self._update_index += 1
        for feature, value in features.items():
            if not value:
                continue
            weights = self.weights[feature]
            weights.update(true, learning_rate * value, self._update_index)
            weights.update(pred, -learning_rate * value, self._update_index)

    def average_weights(self):
        """
        Average all weights over all updates, as a form of regularization
        :return new AveragedPerceptron object with the weights averaged
        """
        print("Averaging weights... ", end="", flush=True)
        started = time.time()
        # Freeze set of features; also allow pickle
        averaged_weights = {feature: weights.average(self._update_index)
                            for feature, weights in self.weights.items()
                            if weights.update_count >= self.min_update}
        averaged = AveragedPerceptron(self.num_labels, weights=averaged_weights)
        averaged.is_frozen = True
        print("Done (%.3fs)." % (time.time() - started))
        return averaged

    def save(self, filename):
        """
        Save all parameters to file
        :param filename: file to write to; the actual written file may have an additional suffix
        """
        print("Saving model to '%s'... " % filename, end="", flush=True)
        started = time.time()
        with shelve.open(filename) as db:
            db["num_labels"] = self.num_labels
            db["min_update"] = self.min_update
            db["weights"] = dict(self.weights)
            db["_update_index"] = self._update_index
            db["is_frozen"] = self.is_frozen
        print("Done (%.3fs)." % (time.time() - started))

    def load(self, filename):
        """
        Load all parameters from file
        :param filename: file to read from; the actual read file may have an additional suffix
        """
        def try_open(*names):
            for f in names:
                # noinspection PyBroadException
                try:
                    return shelve.open(f, flag="r")
                except Exception as e:
                    exception = e
            raise IOError("Model file not found: " + filename) from exception

        print("Loading model from '%s'... " % filename, end="", flush=True)
        started = time.time()
        with try_open(filename, os.path.splitext(filename)[0]) as db:
            self.num_labels = db["num_labels"]
            self.min_update = db["min_update"]
            self.weights.clear()
            self.weights.update(db["weights"])
            self._update_index = db["_update_index"]
            self.is_frozen = db["is_frozen"]
        print("Done (%.3fs)." % (time.time() - started))
