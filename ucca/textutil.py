"""Utility functions for UCCA package."""
from itertools import groupby
from operator import attrgetter

import spacy

from ucca import layer0, layer1


def nlp(*args, **kwargs):
    return get_nlp()(*args, **kwargs)


def get_nlp():
    if nlp.instance is None:
        nlp.instance = spacy.load("en", parser=False, entity=False, matcher=False)
    return nlp.instance
nlp.instance = None


def get_word_vectors(dim=None, size=None):
    vocab = get_nlp().vocab
    if dim is not None and dim != vocab.vectors_length:
        vocab.resize_vectors(dim)
    return {l.orth_: l.vector for l in vocab if l.has_vector and (size is None or l.rank < size)}


def get_tagged(tokens):
    doc = get_nlp().tokenizer.tokens_from_list(tokens)
    get_nlp().tagger(doc)
    return doc


TAG_KEY = "tag"
POS_KEY = "pos"
DEP_KEY = "dep"
HEAD_KEY = "head"


def pos_tag(passage, verbose=False, replace=False):
    """
    POS tag the tokens in the given passage
    :param passage: Passage whose layer 0 nodes will be added the "tag" and "pos" entries in the extra dict
    :param verbose: whether to print tagged text
    :param replace: even if given passage is already POS-tagged, replace existing tags with new ones
    :return: list of tagged terminal nodes
    """
    l0 = passage.layer(layer0.LAYER_ID)
    paragraphs = [sorted(p, key=attrgetter("position")) for _, p in groupby(l0.all, key=attrgetter("paragraph"))]
    tagged = [[(t.text, t.extra.get(TAG_KEY), t.extra.get(POS_KEY)) for t in p] for p in paragraphs]
    if replace or any(tag is None or pos is None for p in tagged for _, tag, pos in p):
        tagged = [[(l.orth_, l.tag_, l.pos_) for l in get_tagged([t.text for t in p])] for p in paragraphs]
        for paragraph, tagged_paragraph in zip(paragraphs, tagged):
            for terminal, (_, tag, pos) in zip(paragraph, tagged_paragraph):
                terminal.extra[TAG_KEY] = tag
                terminal.extra[POS_KEY] = pos
    if verbose:
        print("\n".join(" ".join("%s/%s" % (token, tag) for (token, tag, _) in p) for p in tagged))


SENTENCE_END_MARKS = ('.', '?', '!')


def break2sentences(passage):
    """
    Breaks paragraphs into sentences according to the annotation.

    A sentence is a list of terminals which ends with a mark from
    SENTENCE_END_MARKS, and is also the end of a paragraph or parallel scene.
    :param passage: the Passage object to operate on
    :return: a list of positions in the Passage, each denotes a closing Terminal
        of a sentence.
    """
    l1 = passage.layer(layer1.LAYER_ID)
    terminals = extract_terminals(passage)
    ps_ends = [ps.end_position for ps in l1.top_scenes]
    ps_starts = [ps.start_position for ps in l1.top_scenes]
    marks = [t.position for t in terminals if t.text in SENTENCE_END_MARKS]
    # Annotations doesn't always include the ending period (or other mark)
    # with the parallel scene it closes. Hence, if the terminal before the
    # mark closed the parallel scene, and this mark doesn't open a scene
    # in any way (hence it probably just "hangs" there), it's a sentence end
    marks = [x for x in marks
             if x in ps_ends or ((x - 1) in ps_ends and x not in ps_starts)]
    marks = sorted(set(marks + break2paragraphs(passage)))
    # Avoid punctuation-only sentences
    if len(marks) > 1:
        marks = [x for x, y in zip(marks[:-1], marks[1:])
                 if not all(layer0.is_punct(t) for t in terminals[x:y])] +\
                [marks[-1]]
    return marks


def extract_terminals(p):
    """returns an iterator of the terminals of the passage p"""
    return p.layer(layer0.LAYER_ID).all


def break2paragraphs(passage):
    """
    Breaks into paragraphs according to the annotation.

    Uses the `paragraph' attribute of layer 0 to find paragraphs.
    :param passage: the Passage object to operate on
    :return: a list of positions in the Passage, each denotes a closing Terminal
        of a paragraph.
    """
    terminals = list(extract_terminals(passage))
    paragraph_ends = [(t.position - 1) for t in terminals
                      if t.position != 1 and t.para_pos == 1]
    paragraph_ends.append(terminals[-1].position)
    return paragraph_ends


def indent_xml(xml_as_string):
    """
    Indents a string of XML-like objects.

    This works only for units with no text or tail members, and only for
    strings whose leaves are written as <tag /> and not <tag></tag>.
    :param xml_as_string: XML string to indent
    :return: indented XML string
    """
    tabs = 0
    lines = str(xml_as_string).replace('><', '>\n<').splitlines()
    s = ''
    for line in lines:
        if line.startswith('</'):
            tabs -= 1
        s += ("  " * tabs) + line + '\n'
        if not (line.endswith('/>') or line.startswith('</')):
            tabs += 1
    return s
