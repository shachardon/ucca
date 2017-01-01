from itertools import groupby
from operator import attrgetter

from ucca import layer0

"""Utility functions for POS tagging.
To use the Stanford tagger, download it from http://nlp.stanford.edu/software/tagger.html
After extracting it, set the CLASSPATH environment variable to the target path, and the
STANFORD_MODELS environment variable to the path of the "models" directory therein.
"""

POS_TAG_KEY = "pos_tag"

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


def pos_tag(passage, tagger=None, verbose=False):
    """
    POS tag the tokens in the given passage
    :param passage: Passage whose layer 0 nodes will be added the "pos_tag" entry in the attrib dict
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :return: list of tagged terminal nodes
    """
    l0 = passage.layer(layer0.LAYER_ID)
    for _, paragraph in groupby(l0.all, key=attrgetter("paragraph")):
        terminals = sorted(paragraph, key=attrgetter("position"))
        tagged = get_pos_tagger(tagger).tag([t.text for t in terminals])
        for (terminal, (token, tag)) in zip(terminals, tagged):
            terminal.extra[POS_TAG_KEY] = tag
        if verbose:
            print(" ".join("%s/%s" % (token, tag) for (token, tag) in tagged))
