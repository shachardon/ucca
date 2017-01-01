from itertools import groupby
from operator import attrgetter

from ucca import layer0

"""Utility functions for POS tagging.
To use the Stanford tagger, download it from http://nlp.stanford.edu/software/tagger.html
After extracting it, set the CLASSPATH environment variable to the target path, and the
STANFORD_MODELS environment variable to the path of the "models" directory therein.
"""

POS_TAG_KEY = "pos_tag"
POS_TAGGER_KEY = "pos_tagger"

PERCEPTRON = "perceptron"
STANFORD = "stanford_english_left3words"
STANFORD_BIDI = "stanford_english_bidirectional"

POS_TAGGERS = (PERCEPTRON, STANFORD, STANFORD_BIDI)

INSTANCES = {}


def get_pos_tagger_name(name=None):
    return POS_TAGGERS[0] if name is None else name


def get_pos_tagger(name=None):
    name = get_pos_tagger_name(name)
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
    elif name == STANFORD_BIDI:
        from nltk.tag import StanfordPOSTagger
        return StanfordPOSTagger("english-bidirectional-distsim.tagger")
    else:
        raise ValueError("Invalid POS tagger name: %s" % name)


def pos_tag(passage, tagger=None, verbose=False, replace=False):
    """
    POS tag the tokens in the given passage
    :param passage: Passage whose layer 0 nodes will be added the "pos_tag" entry in the attrib dict
    :param tagger: POS tagger name to use, or None for default
    :param verbose: whether to print tagged text
    :param replace: even if given passage is already POS-tagged with this tagger, replace existing tags with new ones
    :return: list of tagged terminal nodes
    """
    l0 = passage.layer(layer0.LAYER_ID)
    paragraphs = [sorted(paragraph, key=attrgetter("position"))
                  for _, paragraph in groupby(l0.all, key=attrgetter("paragraph"))]
    tagged = [[(t.text, t.extra.get(POS_TAG_KEY)) for t in p] for p in paragraphs]
    if replace or passage.extra.get(POS_TAGGER_KEY) != tagger or any(t is None for p in tagged for _, t in p):
        pos_tagger = get_pos_tagger(tagger)
        tagged = pos_tagger.tag_sents([[t.text for t in p] for p in paragraphs])
        for paragraph, tagged_paragraph in zip(paragraphs, tagged):
            for (terminal, (_, tag)) in zip(paragraph, tagged_paragraph):
                terminal.extra[POS_TAG_KEY] = tag
        passage.extra[POS_TAGGER_KEY] = get_pos_tagger_name(tagger)
    if verbose:
        print("\n".join(" ".join("%s/%s" % (token, tag) for (token, tag) in p) for p in tagged))
