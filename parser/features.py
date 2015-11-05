class FeatureExtractor(object):
    @staticmethod
    def extract_features(state):
        """
        Calculate feature values according to current state
        :param state: current state of the parser
        """
        return {
            "#s": len(state.stack),
            "#b": len(state.buffer),
        }
