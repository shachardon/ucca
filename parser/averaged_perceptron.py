import os
import shelve

import numpy as np


class AveragedPerceptron(object):
    """
    Averaged perceptron to predict parser actions
    """

    def __init__(self, num_actions):
        self.num_actions = num_actions
        self.feature_dictionary = {}
        self.weights = []
        self._last_update = []
        self._totals = []
        self._update_index = 0

    def _get_feature_index(self, feature, frozen=False):
        index = self.feature_dictionary.get(feature)
        if index is None and not frozen:
            self.weights.append(0.01 * np.random.randn(self.num_actions))
            self._last_update.append(np.zeros(self.num_actions, dtype=int))
            self._totals.append(np.zeros(self.num_actions, dtype=float))
            index = len(self.feature_dictionary)
            self.feature_dictionary[feature] = index
        return index

    def _get_feature_indices_and_values(self, features, frozen=False):
        res = [(self._get_feature_index(feature, frozen), value)
               for feature, value in features.items() if value]
        if frozen:
            res = [(index, value) for index, value in res if index is not None]
        return zip(*res)

    def score(self, features):
        """
        Calculate score for each action
        :param features: extracted feature values
        :return: array of score for each action
        """
        is_array = isinstance(self.weights, np.ndarray)
        indices, values = self._get_feature_indices_and_values(features, frozen=is_array)
        if is_array:
            return self.weights[list(indices)].T.dot(values)
        return np.array([sum(self.weights[i][j] * value
                             for i, value in zip(indices, values))
                         for j in range(self.num_actions)])
        # TODO check speed of keeping self.weights as an array and using vstack/append

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
        indices, values = self._get_feature_indices_and_values(features)
        for index, value in zip(indices, values):
            update_feature(index, true_action.id, learning_rate * value)
            update_feature(index, pred_action.id, -learning_rate * value)

    def average_weights(self):
        """
        Average all weights over all updates, as a form of regularization
        Locks the weights matrix to a numpy array
        """
        n = np.array(self._update_index) - self._last_update
        self._totals += + n * self.weights
        self.weights = self._totals / self._update_index

    def save(self, filename):
        with shelve.open(filename) as db:
            db["feature_dictionary"] = self.feature_dictionary
            db["weights"] = self.weights

    def load(self, filename):
        with shelve.open(filename) as db:
            if not db:
                raise IOError("Model file not found or is empty: " + filename)
            self.weights = db["weights"]
            self.feature_dictionary = db["feature_dictionary"]
