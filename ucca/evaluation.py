"""
The evaluation library for UCCA layer 1.
v1.2
2016-12-25: move common Fs to root before evaluation
2017-01-04: flatten centers, do not add 1 (for root) to mutual
2017-01-16: fix bug in moving common Fs
2018-04-12: exclude punctuation nodes regardless of edge tag
"""
from collections import Counter, OrderedDict

from operator import attrgetter

from ucca import layer0, layer1, normalization
from ucca.constructions import get_by_names, create_passage_yields, PRIMARY, DEFAULT, ALL_EDGES
from ucca.layer1 import EdgeTags, NodeTags

UNLABELED = "unlabeled"
WEAK_LABELED = "weak_labeled"
LABELED = "labeled"

EVAL_TYPES = (LABELED, UNLABELED, WEAK_LABELED)

# Pairs that are considered as equivalent for the purposes of evaluation
EQUIV = ((EdgeTags.Process, EdgeTags.State),
         (EdgeTags.ParallelScene, EdgeTags.Center),
         (EdgeTags.Connector, EdgeTags.Linker),
         (EdgeTags.Function, EdgeTags.Relator))


def get_yield(unit):
    try:
        return frozenset(t.position for t in unit.get_terminals(punct=False))
    except ValueError:
        return frozenset()


def move_functions(p1, p2):
    """
    Move any common Fs to the root
    """
    f1, f2 = [{get_yield(u): u for u in p.layer(layer1.LAYER_ID).all
               if u.tag == NodeTags.Foundational and u.ftag == EdgeTags.Function} for p in (p1, p2)]
    for positions in f1.keys() & f2.keys():
        for (p, unit) in ((p1, f1[positions]), (p2, f2[positions])):
            for parent in unit.parents:
                tag = unit.ftag
                parent.remove(unit)
                p.layer(layer1.LAYER_ID).heads[0].add(tag, unit)


def get_text(p, positions):
    l0 = p.layer(layer0.LAYER_ID)
    return [l0.by_position(i).text for i in range(1, len(l0.all) + 1) if i in positions]


def print_tags_and_text(p, yield_tags):
    for y, tags in sorted(yield_tags.items(), key=lambda x: min(x[0] or [0])):
        text = " ".join(get_text(p, y))
        print((",".join(sorted(filter(None, tags))) + ": " + text) if tags else text)


def expand_equivalents(tag_set):
    """
    Returns a set of all the tags in the tag set or those equivalent to them
    :param tag_set: set of tags (strings) to expand
    """
    return tag_set.union(t1 for t in tag_set for pair in EQUIV for t1 in pair if t in pair and t != t1)


class Evaluator:
    def __init__(self, verbose, constructions, units, fscore, errors):
        """
        :param verbose: whether to print the scores
        :param constructions: names of construction types to include in the evaluation
        :param units: whether to calculate and print the mutual and exclusive units in the passages
        :param fscore: whether to find and return the scores
        :param errors: whether to calculate and print the confusion matrix of errors
        """
        self.verbose = verbose
        self.constructions = list(DEFAULT.values()) + [c for c in get_by_names(constructions)
                                                       if c not in DEFAULT.values()]
        self.units = units
        self.fscore = fscore
        self.errors = errors

        self.mutual = OrderedDict()
        self.error_counters = OrderedDict()

    def find_mutuals(self, m1, m2, eval_type, construction):
        mutual_tags = self.mutual.setdefault(construction, {})
        for y in m1.keys() & m2.keys():
            if eval_type == UNLABELED:
                mutual_tags[y] = ()
            else:
                tags = [set(m1[y]), set(m2[y])]
                if eval_type == WEAK_LABELED:
                    tags[0] = expand_equivalents(tags[0])
                intersection = set.intersection(*tags)
                if intersection:  # non-empty intersection
                    mutual_tags[y] = intersection
                elif self.errors:
                    self.error_counters.setdefault(eval_type, {}).setdefault(construction, Counter())[
                        tuple("|".join(sorted(t)) for t in tags)] += 1

    def get_scores(self, p1, p2, eval_type, r=None):
        """
        prints the relevant statistics and f-scores. eval_type can be 'unlabeled', 'labeled' or 'weak_labeled'.
        calculates a set of all the yields such that both passages have a unit with that yield.
        :param p1: passage to compare
        :param p2: reference passage object
        :param eval_type: evaluation type to use, out of EVAL_TYPES
        1. UNLABELED: it doesn't matter what labels are there.
        2. LABELED: also requires tag match (if there are multiple units with the same yield, requires one match)
        3. WEAK_LABELED: also requires weak tag match (if there are multiple units with the same yield,
                         requires one match)
        :param r: reference passage for fine-grained evaluation
        :returns EvaluatorResults object if self.fscore is True, otherwise None
        """
        self.mutual.clear()
        self.error_counters.clear()
        reference_yield_tags = None if r is None else create_passage_yields(r, punct=True)[ALL_EDGES.name]
        maps = [{}, create_passage_yields(p2, self.constructions,
                                          reference_yield_tags=reference_yield_tags)]
        if p1 is not None:
            maps[0] = create_passage_yields(p1, self.constructions,
                                            reference=p2, reference_yield_tags=reference_yield_tags)
            ordered_constructions = [c for c in self.constructions if c in maps[0] or c in maps[1]]
            ordered_constructions += [c for c in maps[1] if c not in ordered_constructions]
            ordered_constructions += [c for c in maps[0] if c not in ordered_constructions]
            for construction in ordered_constructions:
                yield_tags1 = maps[0].get(construction, {})
                yield_tags2 = maps[1].get(construction, {})
                self.find_mutuals(yield_tags1, yield_tags2, eval_type, construction)

        if self.verbose:
            print("Evaluation type: (" + eval_type + ")")

        only = [{c: {y: tags for y, tags in d.items() if y not in self.mutual[c]} for c, d in m.items()} for m in maps]
        if self.verbose and self.units and p1 is not None:
            print("==> Mutual Units:")
            print_tags_and_text(p1, self.mutual[PRIMARY])
            print("==> Only in guessed:")
            print_tags_and_text(p1, only[0][PRIMARY])
            print("==> Only in reference:")
            print_tags_and_text(p2, only[1][PRIMARY])

        error_counters = self.error_counters.get(eval_type, {})
        res = EvaluatorResults((c, SummaryStatistics(len(self.mutual[c]),
                                                     len(only[0].get(c, ())),
                                                     len(only[1].get(c, ())),
                                                     error_counters.get(c)))
                               for c in self.mutual)
        if self.verbose:
            if self.fscore:
                res.print()
            if self.errors and error_counters:
                res.print_confusion_matrix()

        return res


class Scores:
    def __init__(self, evaluator_results, name=None, evaluation_format=None):
        """
        :param evaluator_results: dict: eval_type -> EvaluatorResults
        :param name: if not UCCA, name of evaluated format
        :param evaluation_format: if not ucca, lowercase string representation of evaluated format
        """
        self.evaluators = dict(evaluator_results)
        self.name = name or "UCCA"
        self.format = evaluation_format or "ucca"

    def average_f1(self, mode=LABELED):
        """
        Calculate the average F1 score across primary and remote edges
        :param mode: LABELED, UNLABELED or WEAK_LABELED
        :return: a single number, the average F1
        """
        return float(self[mode].aggregate_default().f1)

    @staticmethod
    def aggregate(scores):
        """
        Aggregate multiple Scores instances
        :param scores: iterable of Scores
        :return: new Scores with aggregated scores
        """
        scores = list(scores)
        evaluators = [s.evaluators for s in scores]
        names = list(set(s.name for s in scores))
        formats = list(set(s.format for s in scores))
        return Scores(((t, EvaluatorResults.aggregate(filter(None, (e.get(t) for e in evaluators))))
                       for t in EVAL_TYPES),
                      name=names[0] if len(names) == 1 else None,
                      evaluation_format=formats[0] if len(formats) == 1 else None)

    def print(self, **kwargs):
        for eval_type in EVAL_TYPES:
            evaluator = self.evaluators.get(eval_type)
            if evaluator:
                print("Evaluation type: (" + eval_type + ")", **kwargs)
                evaluator.print(**kwargs)

    def print_confusion_matrix(self, *args, **kwargs):
        for eval_type in EVAL_TYPES:
            evaluator = self.evaluators.get(eval_type)
            if evaluator:
                evaluator.print_confusion_matrix("Evaluation type: (" + eval_type + ")", *args, **kwargs)

    def fields(self, eval_type=LABELED):
        e = self[eval_type]
        return ["%.3f" % float(getattr(x, y)) for x in e.results.values() for y in ("p", "r", "f1")]

    def titles(self, eval_type=LABELED):
        return self.field_titles(self[eval_type].results.keys(), eval_type=eval_type)

    @staticmethod
    def field_titles(constructions=DEFAULT, eval_type=LABELED):
        return ["_".join(((str(x),) if len(constructions) > 1 else ()) + (eval_type, y))
                for x in constructions for y in ("precision", "recall", "f1")]

    def __getitem__(self, eval_type):
        return self.evaluators[eval_type]


class EvaluatorResults:
    def __init__(self, results, default=None):
        """
        :param results: dict: Construction -> SummaryStatistics
        :param default: map of default constructions (default is primary and remote)
        """
        self.default = default or DEFAULT
        self.results = OrderedDict(results)
        self.results.update(((c, self[c]) for c in self.default.values()))  # Make sure there are entries for defaults

    def print(self, **kwargs):
        for construction, stats in self.results.items():
            if len(self.results) > 1:
                print("\n%s:" % construction.description, **kwargs)
            stats.print(**kwargs)
        print(**kwargs)

    def print_confusion_matrix(self, prefix=None, sep=None, **kwargs):
        primary = self[PRIMARY]
        if primary.errors:
            errors = primary.errors.most_common()
            if sep:
                print(sep.join(("guessed", "ref", "count")), **kwargs)
                for error, freq in errors:
                    print(sep.join(error + (str(freq),)), **kwargs)
            else:
                print("\n%sConfusion Matrix:" % ("" if prefix is None else (prefix + ", ")), **kwargs)
                for error, freq in errors:
                    l1 = max(len(e1) for e1, _ in primary.errors)
                    l2 = max(len(e2) for _, e2 in primary.errors)
                    print("%-*s %-*s %d" % (l1, error[0], l2, error[1], freq), **kwargs)

    @classmethod
    def aggregate(cls, results):
        """
        :param results: iterable of EvaluatorResults
        :return: new EvaluatorResults with aggregates scores
        """
        collected = OrderedDict()
        default = OrderedDict()
        for evaluator_results in results:
            for c, r in evaluator_results.results.items():
                collected.setdefault(c, []).append(r)
            default.update(evaluator_results.default)
        return EvaluatorResults(((c, SummaryStatistics.aggregate(r)) for c, r in collected.items()), default=default)

    def aggregate_default(self):
        """
        Aggregate primary and remote SummaryStatistics in this EvaluatorResults instance
        :return: SummaryStatistics object representing aggregation over primary and remote
        """
        return SummaryStatistics.aggregate([self[c] for c in self.default.values()])

    def __bool__(self):
        return bool(self.results and any(self.results.values()))

    def __getitem__(self, construction):
        return self.results.get(construction, SummaryStatistics(0, 0, 0, Counter()))


class SummaryStatistics:
    def __init__(self, num_matches, num_only_guessed, num_only_ref, errors=None):
        self.num_matches = num_matches
        self.num_only_guessed = num_only_guessed
        self.num_only_ref = num_only_ref
        self.num_guessed = num_matches + num_only_guessed
        self.num_ref = num_matches + num_only_ref
        self.p = 1.0 if self.num_guessed == 0 else 1.0 * num_matches / self.num_guessed
        self.r = 1.0 if self.num_ref == 0 else 1.0 * num_matches / self.num_ref
        self.f1 = 0.0 if 0.0 in (self.p, self.r) else 2.0 * self.p * self.r / float(self.p + self.r)
        self.errors = errors

    def print(self, **kwargs):
        print("Precision: {:.3} ({}/{})".format(self.p, self.num_matches, self.num_guessed), **kwargs)
        print("Recall: {:.3} ({}/{})".format(self.r, self.num_matches, self.num_ref), **kwargs)
        print("F1: {:.3}".format(self.f1), **kwargs)

    @classmethod
    def aggregate(cls, stats):
        """
        :param stats: iterable of SummaryStatistics
        :return: new SummaryStatistics with aggregated scores
        """
        return SummaryStatistics(*map(sum, [map(attrgetter(attr), stats)
                                            for attr in ("num_matches", "num_only_guessed", "num_only_ref")]),
                                 Counter({k: sum((s.errors or {}).get(k, 0) for s in stats)
                                          for k in set.union(*[set(s.errors or ()) for s in stats])}))

    def __bool__(self):
        return bool(self.num_matches or self.num_only_guessed or self.num_only_ref or self.errors)


def evaluate(guessed, ref, converter=None, verbose=False, constructions=DEFAULT,
             units=False, fscore=True, errors=False, normalize=True, eval_type=None, ref_yield_tags=None, **kwargs):
    """
    Compare two passages and return requested diagnostics and scores, possibly printing them too.
    NOTE: since normalize=True by default, this method is destructive: it modifies the given passages before evaluation.
    :param guessed: Passage object to evaluate
    :param ref: reference Passage object to compare to
    :param converter: optional function to apply to passages before evaluation
    :param verbose: whether to print the results
    :param constructions: names of construction types to include in the evaluation
    :param units: whether to evaluate common units
    :param fscore: whether to compute precision, recall and f1 score
    :param errors: whether to print the mistakes
    :param normalize: flatten centers and move common functions to root before evaluation - modifies passages
    :param eval_type: specific evaluation type to limit to
    :param ref_yield_tags: reference passage for fine-grained evaluation
    :return: Scores object
    """
    del kwargs
    if converter is not None:
        guessed = converter(guessed)
        ref = converter(ref)
    if normalize:
        for passage in (guessed, ref):
            normalization.normalize(passage)  # flatten Cs inside Cs
        move_functions(guessed, ref)  # move common Fs to be under the root

    evaluator = Evaluator(verbose, constructions, units, fscore, errors)
    return Scores((evaluation_type, evaluator.get_scores(guessed, ref, evaluation_type, r=ref_yield_tags))
                  for evaluation_type in ([eval_type] if eval_type else EVAL_TYPES))
