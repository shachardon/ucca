import numpy as np

from config import Config


class Perceptron(object):
    """
    Averaged perceptron to predict parser actions
    """

    def __init__(self, num_actions, num_features):
        if Config().seed:
            np.random.seed(int(Config().seed))

        self.weights = 0.01 * np.random.randn(num_actions, num_features)

    def score(self, features):
        """
        Calculate score for each action
        :param features: extracted feature values
        :return: array of score for each action
        """
        return self.weights.dot(features)

    def update(self, features, pred_action, true_action):
        """
        Update classifier weights according to predicted and true action
        :param features: extracted feature values
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :return: True if update was needed, False if predicted and true actions were the same
        """
        if pred_action == true_action:
            return False
        self.weights[true_action.id] += features
        self.weights[pred_action.id] -= features
        return True
