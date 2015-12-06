import os
import shelve
import time
from collections import defaultdict

import numpy as np


class AveragedPerceptron(object):
    """
    Averaged perceptron to predict parser actions
    """

    def __init__(self, num_actions):
        self.num_actions = num_actions
        self.weights = defaultdict(lambda: 0.01 * np.random.randn(self.num_actions))
        self._last_update = defaultdict(lambda: np.zeros(self.num_actions, dtype=int))
        self._totals = defaultdict(lambda: np.zeros(self.num_actions, dtype=float))
        self._update_index = 0
        self.is_averaged = False

    def score(self, features):
        """
        Calculate score for each action
        :param features: extracted feature values
        :return: array of score for each action
        """
        scores = np.zeros(self.num_actions)
        for feature, value in features.items():
            if not value:
                continue
            weights = self.weights.get(feature)
            if weights is None:
                continue
            scores += value * weights
        return scores

    def update(self, features, pred_action, true_action, learning_rate=1):
        """
        Update classifier weights according to predicted and true action
        :param features: extracted feature values
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :param learning_rate: how much to scale the feature vector for the weight update
        """
        def update_feature(f, a, v):
            n = self._update_index - self._last_update[f][a]
            self._totals[f][a] += n * self.weights[f][a]
            self.weights[f][a] += v
            self._last_update[f][a] = self._update_index

        self._update_index += 1
        for feature, value in features.items():
            if not value:
                continue
            update_feature(feature, true_action.id, learning_rate * value)
            update_feature(feature, pred_action.id, -learning_rate * value)

    def average_weights(self):
        """
        Average all weights over all updates, as a form of regularization
        """
        print("Averaging weights... ", end="", flush=True)
        started = time.time()
        for feature in self.weights:
            n = self._update_index - self._last_update[feature]
            self._totals[feature] += n * self.weights[feature]
            self.weights[feature] = self._totals[feature] / self._update_index
        self.weights = dict(self.weights)  # "Lock" set of features; also allow pickle
        self.is_averaged = True
        print("Done (%.3fs)." % (time.time() - started))

    def save(self, filename, intermediate=False):
        print("Saving %s model to '%s'... " % (
            "intermediate" if intermediate else "final", filename), end="", flush=True)
        started = time.time()
        with shelve.open(filename) as db:
            if intermediate:
                db["intermediate"] = {
                    "weights": dict(self.weights),
                    "_last_update": dict(self._last_update),
                    "_totals": dict(self._totals),
                    "_update_index": self._update_index,
                }
            else:
                db.pop("intermediate", None)
                db["weights"] = self.weights
        print("Done (%.3fs)." % (time.time() - started))

    def load(self, filename, intermediate=False):
        def try_open(*names):
            for f in names:
                # noinspection PyBroadException
                try:
                    return shelve.open(f, flag="r")
                except Exception as e:
                    exception = e
            raise IOError("Model file not found: " + filename) from exception

        print("Loading %s model from '%s'... " % (
            "intermediate" if intermediate else "final", filename), end="", flush=True)
        started = time.time()
        with try_open(filename, os.path.splitext(filename)[0]) as db:
            if intermediate:
                self.weights.update(db["intermediate"]["weights"])
                self._last_update.update(db["intermediate"]["_last_update"])
                self._totals.update(db["intermediate"]["_totals"])
                self._update_index = db["intermediate"]["_update_index"]
            else:
                self.weights = db["weights"]
        print("Done (%.3fs)." % (time.time() - started))
