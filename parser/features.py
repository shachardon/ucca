class FeatureExtractor(object):
    def __init__(self):
        self.features = {
            "#s": lambda state: len(state.stack),
            "#b": lambda state: len(state.buffer)
        }

    def extract_features(self, state):
        """
        Calculate feature values according to current state
        :param state: current state of the parser
        """
        return {feature: f(state) for feature, f in self.features.items()}
