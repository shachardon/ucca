import numpy as np


class Classifier(object):
    def __init__(self, actions):
        self.actions = actions
        self.actions_reverse = {str(action): i for i, action in enumerate(self.actions)}

        self.features = [
            lambda state: len(state.stack),
            lambda state: len(state.buffer)
        ]
        self.feature_values = None
        self.weights = 0.01 * np.random.randn(len(self.actions), len(self.features))

    def calc_features(self, state):
        """
        Calculate feature values according to current state
        """
        self.feature_values = np.array([f(state) for f in self.features])

    def predict_action(self, state):
        """
        Choose action based on classifier
        Assume self.feature_values have already been calculated
        :return: legal action with maximum probability according to classifier
        """
        scores = self.weights.dot(self.feature_values)
        best_action = self.actions[np.argmax(scores)]
        if state.is_legal(best_action):
            return best_action
        actions = (self.actions[i] for i in np.argsort(scores)[-2::-1])  # Exclude max, already checked
        try:
            return next(action for action in actions if state.is_legal(action))
        except StopIteration as e:
            raise Exception("No legal actions available") from e

    def update(self, pred_action, true_action):
        """
        Update classifier weights according to predicted and true action
        Assume self.feature_values have already been calculated
        :param pred_action: action predicted by the classifier
        :param true_action: action returned by oracle
        :return: True if update was needed, False if predicted and true actions were the same
        """
        if pred_action == true_action:
            return False
        self.weights[self.actions_reverse[str(true_action)]] += self.feature_values
        self.weights[self.actions_reverse[str(pred_action)]] -= self.feature_values
        return True
