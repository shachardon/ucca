import pickle
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

    def update(self, features, pred_action, true_action):
        """
        Update classifier weights according to predicted and true action
        :param features: extracted feature values
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :return: True if update was needed, False if predicted and true actions were the same
        """
        def update_feature(f, a, v):
            n = self._update_index - self._last_update[f][a]
            self._totals[f][a] += n * self.weights[f][a]
            self.weights[f][a] += v
            self._last_update[f][a] = self._update_index

        if pred_action == true_action:
            return False

        self._update_index += 1
        for feature, value in features.items():
            if not value:
                continue
            update_feature(feature, true_action.id, value)
            update_feature(feature, pred_action.id, -value)

        return True

    def average_weights(self):
        """
        Average all weights over all updates, as a form of regularization
        """
        for feature in self.weights:
            n = self._update_index - self._last_update[feature]
            self._totals[feature] += n * self.weights[feature]
            self.weights[feature] = self._totals[feature] / self._update_index
        self.weights = dict(self.weights)  # "Lock" set of features; also allow pickle

    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self.weights, f)

    def load(self, filename):
        with open(filename, "rb") as f:
            self.weights = pickle.load(f)
