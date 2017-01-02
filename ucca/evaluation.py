"""
The evaluation library for UCCA layer 1.
v1.1
2016-12-25: move common Fs to root before evaluation
"""
from collections import Counter, defaultdict
from operator import attrgetter

from ucca import layer0, layer1
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

EXCLUDED = (EdgeTags.Punctuation,
            EdgeTags.LinkArgument,
            EdgeTags.LinkRelation,
            EdgeTags.Terminal)


def flatten_centers(p):
    """
    If there are Cs inside Cs in layer1, remove the external C.
    :param p: Passage object to flatten
    """
    def _center_children(u):
        return [x for x in u.children if x.tag == NodeTags.Foundational and x.ftag == EdgeTags.Center]

    to_ungroup = [u for u in p.layer(layer1.LAYER_ID).all if u.tag == NodeTags.Foundational and u.ftag == EdgeTags.Center and
                  len(_center_children(u)) == 1 and (u.fparent is None or len(_center_children(u.fparent)) == 1)]
    for unit in to_ungroup:
        ungroup(unit)


def ungroup(unit):
    """
    If the unit has an fparent, removes the unit and adds its children to that parent.
    :param unit: Node object to potentially remove
    """
    fparent = unit.fparent
    if fparent is not None:
        if len(unit.parents) > 1:
            if len(unit.centers) == 1:  # if there is only one child, assign that child as the parent's child
                for e in unit.incoming:
                    if e.attrib.get("remote"):
                        e.parent.add(e.tag, unit.centers[0], edge_attrib=e.attrib)
            else:
                return  # don't ungroup if there is more than one parent and no single center
        for e in unit.outgoing:
            fparent.add(e.tag, e.child, edge_attrib=e.attrib)
    unit.destroy()


def move_functions(p1, p2):
    """
    Move any common Fs to the root
    """
    f1, f2 = [{get_yield(u): u for u in p.layer(layer1.LAYER_ID).all
               if u.tag == NodeTags.Foundational and u.ftag == EdgeTags.Function}
              for p in (p1, p2)]
    for positions, unit1 in f1.items():
        unit2 = f2.get(positions)
        if unit2 is not None:
            for (p, unit) in ((p1, unit1), (p2, unit2)):
                move(unit, p.layer(layer1.LAYER_ID).heads[0])


def move(unit, new_parent):
    for parent in unit.parents:
        parent.remove(unit)
    new_parent.add(unit.ftag, unit)
    

def get_text(p, positions):
    l0 = p.layer(layer0.LAYER_ID)
    return [l0.by_position(i).text for i in sorted(positions.intersection(range(1, len(l0.all) + 1)))]


def create_passage_yields(p, remotes=False, implicit=False):
    """
    :param p: Passage to find yields of
    :param remotes: if True, regular table includes remotes
    :param implicit: if True, regular table includes the empty yield of implicit nodes
    :returns two dicts:
    1. maps a set of terminal indices (excluding punctuation) to a list of layer1 edges whose yield (excluding remotes
       and punctuation) is that set.
    2. maps a set of terminal indices (excluding punctuation) to a set of remote edges whose yield (excluding remotes
       and punctuation) is that set.
    """
    l1 = p.layer(layer1.LAYER_ID)
    edges = (e for n in l1.all for e in n if e.tag not in EXCLUDED and
             (implicit or not e.child.attrib.get("implicit")))

    table_reg, table_remote = defaultdict(list), defaultdict(list)
    for edge in edges:
        table = table_remote if edge.attrib.get("remote") else table_reg
        table[get_yield(edge.child, remotes)].append(edge.tag)

    return table_reg, table_remote


def find_mutuals(m1, m2, eval_type):
    mutual_tags = dict()
    error_counter = Counter()
    for y in m1.keys() & m2.keys():
        if eval_type == UNLABELED:
            mutual_tags[y] = ()
        else:
            tags1 = set(m1[y])
            tags2 = set(m2[y])
            if eval_type == WEAK_LABELED:
                tags1 = expand_equivalents(tags1)
            intersection = tags1 & tags2
            if intersection:  # non-empty intersection
                mutual_tags[y] = intersection
            else:
                error_counter[(str(sorted(tags1)), str(sorted(tags2)))] += 1
    return mutual_tags, error_counter


def print_tags_and_text(p1, tags, y):
    print(",".join(sorted(tags)) + (": " if tags else "") + " ".join(get_text(p1, y)))


def get_yield(unit, remotes=False):
    return frozenset(t.position for t in unit.get_terminals(punct=False, remotes=remotes))


def expand_equivalents(tag_set):
    """
    Returns a set of all the tags in the tag set or those equivalent to them
    :param tag_set: set of tags (strings) to expand
    """
    return tag_set.union(t1 for t in tag_set for pair in EQUIV for t1 in pair if t in pair and t != t1)


class Evaluator(object):
    def __init__(self, verbose, units, fscore, errors):
        """
        :param units: whether to calculate and print the mutual and exclusive units in the passages
        :param fscore: whether to find and return the scores
        :param errors: whether to calculate and print the confusion matrix of errors
        :param verbose: whether to print the scores
        """
        self.verbose = verbose
        self.units = units
        self.fscore = fscore
        self.errors = errors

    def get_scores(self, p1, p2, eval_type, separate_remotes=True):
        """
        prints the relevant statistics and f-scores. eval_type can be 'unlabeled', 'labeled' or 'weak_labeled'.
        calculates a set of all the yields such that both passages have a unit with that yield.
        :param p1: passage to compare
        :param p2: reference passage object
        :param eval_type: evaluation type to use, out of EVAL_TYPES
        1. UNLABELED: it doesn't matter what labels are there.
        2. LABELED: also requires tag match (if there are multiple units with the same yield, requires one match)
        3. WEAK_LABELED: also requires weak tag match (if there are multiple units with the same yield, requires one match)
        :param separate_remotes: whether to put remotes in a separate map
        :returns EvaluatorResults object if self.fscore is True, otherwise None
        """
        map2, map2_remotes = create_passage_yields(p2, not separate_remotes)

        all2 = set(map2.keys())
        all2_remote = set(map2_remotes.keys())
        if p1 is None:
            mutual = mutual_remote = dict()
            all1 = all1_remote = set()
            error_counter = Counter()
        else:
            map1, map1_remotes = create_passage_yields(p1, not separate_remotes)
            all1 = set(map1.keys())
            all1_remote = set(map1_remotes.keys())
            mutual, error_counter = find_mutuals(map1, map2, eval_type)
            mutual_remote = None
            if separate_remotes:
                mutual_remote, _ = find_mutuals(map1_remotes, map2_remotes, eval_type)

        if self.verbose:
            print("Evaluation type: (" + eval_type + ")")
        res = None

        mutual_ys = set(mutual)
        if self.verbose and self.units and p1 is not None:
            print("==> Mutual Units:")
            for y, tags in mutual.items():
                print_tags_and_text(p1, tags, y)

            print("==> Only in guessed:")
            for y in all1 - mutual_ys:
                print_tags_and_text(p1, map1[y], y)

            print("==> Only in reference:")
            for y in all2 - mutual_ys:
                print_tags_and_text(p2, map2[y], y)

        if self.fscore:
            mutual_ys_remote = set(mutual_remote)
            res = EvaluatorResults(SummaryStatistics(1 + len(mutual),  # Count root as mutual
                                                     len(all1 - mutual_ys),
                                                     len(all2 - mutual_ys)),
                                   SummaryStatistics(len(mutual_remote),
                                                     len(all1_remote - mutual_ys_remote),
                                                     len(all2_remote - mutual_ys_remote)))
            if self.verbose:
                res.print()

        if self.verbose and self.errors and error_counter:
            print("\nConfusion Matrix:\n")
            for error, freq in error_counter.most_common():
                print(error[0], "\t", error[1], "\t", freq)

        return res


class Scores(object):
    def __init__(self, evaluator_results):
        """
        :param evaluator_results: dictionary of eval_type -> EvaluatorResults
        """
        self.evaluators = dict(evaluator_results)

    def average_f1(self, mode=LABELED):
        """
        Calculate the average F1 score across regular/remote edges
        :param mode: LABELED, UNLABELED or WEAK_LABELED
        :return: a single number, the average F1
        """
        return float(self.evaluators[mode].aggregate_all().f1)

    @staticmethod
    def aggregate(scores):
        """
        Aggregate multiple Scores instances
        :param scores: iterable of Scores
        :return: new Scores with aggregated scores
        """
        return Scores((t, EvaluatorResults.aggregate(s.evaluators[t] for s in scores))
                      for t in EVAL_TYPES)

    def aggregate_all(self):
        """
        Aggregate all SummaryStatistics in this Scores instance
        :return: SummaryStatistics representing aggregation over all instances
        """
        return SummaryStatistics.aggregate(s for e in self.evaluators.values()
                                           for s in (e.regular, e.remotes))

    def print(self):
        for eval_type in EVAL_TYPES:
            print("Evaluation type: (" + eval_type + ")")
            self.evaluators[eval_type].print()

    def fields(self):
        e = self.evaluators[LABELED]
        return ["%.3f" % float(getattr(x, y)) for x in (e.regular, e.remotes) for y in ("p", "r", "f1")]

    @staticmethod
    def field_titles():
        return ["%s_labeled_%s" % (x, y) for x in ("regular", "remote") for y in ("precision", "recall", "f1")]


class EvaluatorResults(object):
    def __init__(self, regular, remotes):
        """
        :param regular: SummaryStatistics for regular edges
        :param remotes: SummaryStatistics for remote edges
        """
        self.regular = regular
        self.remotes = remotes

    def print(self):
        print("\nRegular Edges:")
        self.regular.print()

        print("\nRemote Edges:")
        self.remotes.print()
        print()

    @classmethod
    def aggregate(cls, results):
        """
        :param results: iterable of EvaluatorResults
        :return: new EvaluatorResults with aggregates scores
        """
        regular, remotes = zip(*[(r.regular, r.remotes) for r in results])
        return EvaluatorResults(SummaryStatistics.aggregate(regular),
                                SummaryStatistics.aggregate(remotes))

    def aggregate_all(self):
        """
        Aggregate all SummaryStatistics in this EvaluatorResults instance
        :return: SummaryStatistics object representing aggregation over all instances
        """
        return SummaryStatistics.aggregate((self.regular, self.remotes))


class SummaryStatistics(object):
    def __init__(self, num_matches, num_only_guessed, num_only_ref):
        self.num_matches = num_matches
        self.num_only_guessed = num_only_guessed
        self.num_only_ref = num_only_ref
        self.num_guessed = num_matches + num_only_guessed
        self.num_ref = num_matches + num_only_ref
        self.p = "NaN" if self.num_guessed == 0 else 1.0 * num_matches / self.num_guessed
        self.r = "NaN" if self.num_ref == 0 else 1.0 * num_matches / self.num_ref
        for v in (0.0, "NaN"):
            if v in (self.p, self.r):
                self.f1 = v
                return
        self.f1 = 2.0 * self.p * self.r / float(self.p + self.r)

    def print(self):
        print("Precision: {:.3} ({}/{})".format(self.p, self.num_matches, self.num_guessed))
        print("Recall: {:.3} ({}/{})".format(self.r, self.num_matches, self.num_ref))
        print("F1: {:.3}".format(self.f1))

    @classmethod
    def aggregate(cls, stats):
        """
        :param stats: iterable of SummaryStatistics
        :return: new SummaryStatistics with aggregated scores
        """
        return SummaryStatistics(*map(sum, [map(attrgetter(attr), stats)
                                            for attr in ("num_matches", "num_only_guessed", "num_only_ref")]))


def evaluate(guessed_passage, ref_passage, verbose=False, units=False, fscore=True, errors=False):
    """
    :param guessed_passage: Passage object to evaluate
    :param ref_passage: reference Passage object to compare to
    :param verbose: whether to print the results
    :param units: whether to evaluate common units
    :param fscore: whether to compute precision, recall and f1 score
    :param errors: whether to print the mistakes
    :return: Scores object
    """
    # for passage in (guessed_passage, ref_passage):
    #     flatten_centers(passage)  # flatten Cs inside Cs
    move_functions(guessed_passage, ref_passage)  # move common Fs to be under the root

    evaluator = Evaluator(verbose, units, fscore, errors)
    return Scores((evaluation_type, evaluator.get_scores(guessed_passage, ref_passage, evaluation_type))
                  for evaluation_type in EVAL_TYPES)
