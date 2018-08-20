#!/usr/bin/env python3

import argparse
import csv
import os
from unidecode import unidecode
from xml.etree.ElementTree import Element

from ucca.convert import to_site, from_site, SiteCfg, SiteUtil
from ucca.ioutil import get_passages_with_progress_bar, write_passage
from ucca.normalization import normalize
from ucca.textutil import get_tokenizer

desc = """Parses XML files in UCCA standard format, fix tokenization and write back."""


def expand_to_neighboring_punct(i, is_puncts):
    """
    >>> expand_to_neighboring_punct(0, [False, True, True])
    (0, 3)
    >>> expand_to_neighboring_punct(2, [True, True, False])
    (0, 3)
    >>> expand_to_neighboring_punct(1, [False, False, False])
    (1, 2)
    """
    start = i
    end = i + 1
    while start > 0 and is_puncts[start - 1]:
        start -= 1
    while end < len(is_puncts) and is_puncts[end]:
        end += 1
    return start, end


class State:
    def __init__(self):
        self.ID = 1000000

    def get_id(self):
        ret = str(self.ID)
        self.ID += 1
        return ret


def create_token_element(state, text, is_punct):
    elem = Element(SiteCfg.Tags.Terminal, {SiteCfg.Attr.SiteID: state.get_id()})
    elem.text = text
    preterminal_elem = Element(SiteCfg.Tags.Unit,
                               {SiteCfg.Attr.ElemTag: SiteCfg.Types.Punct if is_punct else SiteCfg.TBD,
                                SiteCfg.Attr.SiteID: state.get_id(),
                                SiteCfg.Attr.Unanalyzable: SiteCfg.FALSE,
                                SiteCfg.Attr.Uncertain: SiteCfg.FALSE})
    preterminal_elem.append(elem)
    return preterminal_elem


def insert_punct(insert_index, preterminal_parent, state, punct_tokens):
    for punct_token in punct_tokens:
        punct_elem = create_token_element(state, punct_token, is_punct=True)
        preterminal_parent.insert(insert_index, punct_elem)
        insert_index += 1
    return insert_index


def get_parents(paragraph, elements):
    return [next(x for x in paragraph.iter(SiteCfg.Tags.Unit) if t in x) for t in elements]


def insert_retokenized(terminal, preterminal_parent, tokens, index_in_preterminal_parent, non_punct_index, state):
    terminal.text = tokens[non_punct_index]
    insert_index = insert_punct(index_in_preterminal_parent, preterminal_parent, state, tokens[:non_punct_index])
    insert_punct(insert_index + 1, preterminal_parent, state, tokens[non_punct_index + 1:])


def false_indices(l):
    return [i for i, x in enumerate(l) if not x]


def is_punct(text):
    return all(not c.isalnum() for c in text)


def strip_context(new_context, old_context, start_offset, end_offset):
    """
    >>> strip_context(["I", "'ve", "done"], ["I", "'ve", "done"], 1, 1)
    ["'ve"]
    >>> strip_context(["I", "'ve,", "done"], ["I", "'ve", ",", "done"], 1, 1)
    ["'ve", ","]
    >>> strip_context(["'ve", "done"], ["'", "ve", "done"], 0, 1)
    ["'", "ve"]
    >>> strip_context(["I", "'ve,"], ["I", "'ve", ","], 1, 0)
    ["'ve", ","]
    >>> strip_context(["can", "'t", "see"], ["ca", "n't", "see"], 1, 1)
    ["'t"]
    >>> strip_context(["I", "can", "'t"], ["I", "ca", "n't"], 1, 1)
    ["can"]
    >>> strip_context(["because", "somebody", "'d"], ["because", "somebody'd"], 1, 1)
    []
    >>> strip_context(["somebody", "'d", "always"], ["somebody'd", "always"], 1, 1)
    []
    """
    start = 0
    if start_offset:
        prefix = ""
        while old_context[0].startswith(prefix + new_context[start]):
            prefix += new_context[start]
            start += 1
        diff = len(old_context[0]) - len(prefix)
        if diff:
            if start > 0:
                new_context[start - 1] += new_context[start][:diff]
            new_context[start] = new_context[start][diff:]
    end = len(new_context)
    if end_offset:
        suffix = ""
        while old_context[-1].endswith(new_context[end - 1] + suffix):
            suffix = new_context[end - 1] + suffix
            end -= 1
        diff = len(old_context[-1]) - len(suffix)
        if diff:
            end -= 1
            if end > 0:
                new_context[end - 1] += new_context[end][:-diff]
            new_context[end] = new_context[end][-diff:]
    return new_context[start:end]


END_CLITICS = {"'m", "'ll", "'s", "'ve", "'d", "'re", "n't", "'t"}
START_CLITICS = {"l'", "qu'", "n'", "d'", "s'", "m'", "c'", "t'", "jusqu'", "j'"}


def insert_spaces(tokens):
    for token, next_token in zip(tokens[:-1], tokens[1:]):
        yield token
        if token.lower() not in START_CLITICS and next_token.lower() not in END_CLITICS:
            yield " "
    if tokens:
        yield tokens[-1]


def retokenize(i, start, end, terminals, preterminals, preterminal_parents, passage_id, tokenizer, state, cw):
    start_offset = 0 if start == 0 else 1
    end_offset = 0 if end == len(terminals) else 1
    old_context = [s for t in terminals[start - start_offset:end + end_offset]
                   for s in SiteUtil.unescape(t.text).strip().split()]  # In case a token happens to contain a space
    new_context = [t.orth_ for t in tokenizer("".join(insert_spaces(old_context)))]
    if old_context == new_context:
        return False
    old_tokens = old_context[start_offset:len(old_context) - end_offset]
    new_tokens = strip_context(new_context, old_context, start_offset, end_offset)
    if not new_tokens or old_tokens == new_tokens:
        return False
    non_punct_indices = false_indices(map(is_punct, new_tokens))
    if len(non_punct_indices) == 1:  # Only one token in the sequence is not punctuation
        non_punct_index = non_punct_indices[0]
        new_tokens = (decode_special_chars(new_tokens[:non_punct_index]) + [new_tokens[non_punct_index]] +
                      decode_special_chars(new_tokens[non_punct_index + 1:]))  # Replace special charas in punct
        index_in_preterminal_parent = preterminal_parents[i].getchildren().index(preterminals[i])
        for j in list(range(start, i)) + list(range(i + 1, end)):  # Remove all surrounding punct
            preterminal_parents[j].remove(preterminals[j])
        insert_retokenized(terminals[i], preterminal_parents[i], new_tokens, index_in_preterminal_parent,
                           non_punct_index, state)
        cw.writerow(("Fixed", passage_id, " ".join(old_tokens), " ".join(new_tokens)))
        return True
    cw.writerow(("Unhandled", passage_id, " ".join(old_tokens), " ".join(new_tokens)))
    return False


def decode_special_chars(tokens):  # Replace special chars with ascii variants but only if length is preserved
    return [d if len(t) == len(d) or all(c == "." for c in d) else t
            for t, d in zip(tokens, (unidecode(t) for t in tokens))]


def fix_tokenization(passage, lang, cw):
    tokenizer = get_tokenizer(lang=lang)
    elem = to_site(passage)
    state = State()
    ever_changed = False
    for paragraph in elem.iterfind(SiteCfg.Paths.Paragraphs):
        while True:
            changed = False
            terminals = list(paragraph.iter(SiteCfg.Tags.Terminal))
            preterminals = get_parents(paragraph, terminals)
            preterminal_parents = get_parents(paragraph, preterminals)
            is_puncts = [p.get(SiteCfg.Attr.ElemTag) == SiteCfg.Types.Punct for p in preterminals]
            for i in false_indices(is_puncts):
                start, end = expand_to_neighboring_punct(i, is_puncts)
                if retokenize(i, start, end, terminals, preterminals, preterminal_parents, passage.ID, tokenizer, state,
                              cw):
                    ever_changed = changed = True
                    break
            if not changed:
                break
    return from_site(elem) if ever_changed else None


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    with open(args.logfile, "w", newline="", encoding="utf-8") as outfile:
        cw = csv.writer(outfile)
        for passage in get_passages_with_progress_bar(args.filenames, "Fixing tokenization"):
            fixed = fix_tokenization(passage, lang=args.lang, cw=cw)
            if fixed is not None:
                outfile.flush()
                normalize(fixed)
                write_passage(fixed, outdir=args.outdir, binary=args.binary, prefix=args.prefix, verbose=args.verbose)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="passage file names to convert")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-O", "--logfile", default="fix_tokenization.csv", help="output log file")
    argparser.add_argument("-l", "--lang", default="en", help="language two-letter code for sentence model")
    argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
    argparser.add_argument("-b", "--binary", action="store_true", help="write in pickle binary format (.pickle)")
    argparser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    main(argparser.parse_args())
