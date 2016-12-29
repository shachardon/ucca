"""Utility functions for POS tagging.
To use the Stanford tagger, download it from http://nlp.stanford.edu/software/tagger.html
After extracting it, set the CLASSPATH environment variable to the target path, and the
STANFORD_MODELS environment variable to the path of the "models" directory therein.
"""

PERCEPTRON = "perceptron"
STANFORD = "stanford_english_left3words"

POS_TAGGERS = (PERCEPTRON, STANFORD)

INSTANCES = {}


def get_pos_tagger(name=None):
    if name is None:
        name = POS_TAGGERS[0]
    tagger = INSTANCES.get(name)
    if tagger is None:
        tagger = _init_pos_tagger(name)
        INSTANCES[name] = tagger
    return tagger


def _init_pos_tagger(name):
    if name == PERCEPTRON:
        from nltk.tag import PerceptronTagger
        return PerceptronTagger()
    elif name == STANFORD:
        from nltk.tag import StanfordPOSTagger
        return StanfordPOSTagger("english-left3words-distsim.tagger")
    else:
        raise ValueError("Invalid POS tagger name: %s" % name)
