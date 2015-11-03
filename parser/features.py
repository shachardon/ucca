class FeatureExtractor(object):
    def __init__(self):
        self.features = [
            lambda state: len(state.stack),
            lambda state: len(state.buffer)
        ]

    def extract_features(self, state):
        """
        Calculate feature values according to current state
        :param state: current state of the parser
        """
        return [f(state) for f in self.features]
