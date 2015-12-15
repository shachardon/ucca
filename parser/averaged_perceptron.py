import os
import shelve
import time
from collections import defaultdict

import numpy as np


class Weights(object):
    def __init__(self, num_actions, weights=None):
        self.num_actions = num_actions
        if weights is None:
            self.weights = 0.01 * np.random.randn(num_actions)
            self._last_update = np.zeros(num_actions, dtype=int)
            self._totals = np.zeros(num_actions, dtype=float)
        else:
            self.weights = weights

    def update(self, action, value, update_index):
        n = update_index - self._last_update[action]
        self._totals[action] += n * self.weights[action]
        self.weights[action] += value
        self._last_update[action] = update_index

    def average(self, update_index):
        """
        Average weights over all updates
        :param update_index: number of updated to average over
        :return new Weights object with the weights averaged
        """
        n = update_index - self._last_update
        totals = self._totals + n * self.weights
        averaged_weights = totals / update_index
        return Weights(self.num_actions, averaged_weights)


class AveragedPerceptron(object):
    """
    Averaged perceptron to predict parser actions
    """

    def __init__(self, num_actions, weights=None):
        self.num_actions = num_actions
        self.weights = defaultdict(lambda: Weights(num_actions))
        self._update_index = 0
        self.is_averaged = False
        if weights is not None:
            self.weights.update(weights)

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
            scores += value * weights.weights
        return scores

    def update(self, features, pred_action, true_action, learning_rate=1):
        """
        Update classifier weights according to predicted and true action
        :param features: extracted feature values
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :param learning_rate: how much to scale the feature vector for the weight update
        """
        self._update_index += 1
        for feature, value in features.items():
            if not value:
                continue
            weights = self.weights[feature]
            weights.update(true_action.id, learning_rate * value, self._update_index)
            weights.update(pred_action.id, -learning_rate * value, self._update_index)

    def average_weights(self):
        """
        Average all weights over all updates, as a form of regularization
        :return new AveragedPerceptron object with the weights averaged
        """
        print("Averaging weights... ", end="", flush=True)
        started = time.time()
        # "Lock" set of features; also allow pickle
        averaged_weights = {feature: weights.average(self._update_index)
                            for feature, weights in self.weights.items()}
        averaged = AveragedPerceptron(self.num_actions, averaged_weights)
        averaged.is_averaged = True
        print("Done (%.3fs)." % (time.time() - started))
        return averaged

    def save(self, filename):
        print("Saving model to '%s'... " % filename, end="", flush=True)
        started = time.time()
        with shelve.open(filename) as db:
            db["num_actions"] = self.num_actions
            db["weights"] = dict(self.weights)
            db["_update_index"] = self._update_index
            db["is_averaged"] = self.is_averaged
        print("Done (%.3fs)." % (time.time() - started))

    def load(self, filename):
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
            self.num_actions = db["num_actions"]
            self.weights.clear()
            self.weights.update(db["weights"])
            self._update_index = db["_update_index"]
            self.is_averaged = db["is_averaged"]
        print("Done (%.3fs)." % (time.time() - started))
