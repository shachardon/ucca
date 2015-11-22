#!/usr/bin/python3
"""
The evaluation software for UCCA layer 1.
"""

from ucca import convert
# import ucca_db
from xml.etree.ElementTree import ElementTree
from optparse import OptionParser
from collections import Counter


EQUIV = [["P", "S"], ["H", "C"], ["N", "L"]]  # Pairs that are considered as equivalent for the purposes of evaluation
#RELATORS = ["that", "than", "who", "what", "to", "how", "of"]

#######################################################################################
# UTILITY METHODS
#######################################################################################


def flatten_centers(p):
    """If there are Cs inside Cs in layer1 of passage C, cancel the external C."""
    def _center_children(u):
        return [x for x in u.children if x.tag == "FN" and x.ftag == "C"]

    to_ungroup = []
    for unit in p.layer("1").all:
        if unit.tag == "FN" and unit.ftag == "C":
            parent = unit.fparent
            if len(_center_children(unit)) == 1 and\
                    (parent is None or len(_center_children(parent)) == 1):
                to_ungroup.append(unit)

    # debug
    # pr = [(u, u.fparent) for u in to_ungroup]
    # for x, p in pr:
    #     print('\n'.join([str(x), str(p)]))

    for unit in to_ungroup:
        ungroup(unit)

    # print('\n\n')
    # print('\n'.join([str(x[1]) for x in pr]))


def ungroup(x):
    """
    If the unit has an fparent, removes the unit and adds its children to that parent.
    """
    if x.tag != "FN":
        return None
    fparent = x.fparent
    if fparent is not None:
        if len(x.parents) > 1:
            if len(x.centers) == 1:  # if there is only one child, assign that child as the 
                for e in x.incoming:
                    if e.attrib.get("remote"):
                        e.parent.add(e.tag, x.centers[0], edge_attrib=e.attrib)
            else:
                return None  # don't ungroup if there is more than one parent and no single center
        for e in x.outgoing:
            fparent.add(e.tag, e.child, edge_attrib=e.attrib)
    x.destroy()
    return fparent


def to_text(p, terms):
    """Returns a text representation of the terminals whose terminals are in terms"""
    l = sorted(list(terms))
    words = get_text(p, l)
    pre_context = get_text(p, range(min(l) - 3, min(l)))
    post_context = get_text(p, range(max(l) + 1, max(l) + 3))
    return ' '.join(pre_context) + ' { ' + ' '.join(words) + ' } ' + ' '.join(post_context)


def mutual_yields(passage1, passage2, eval_type, separate_remotes=True):
    """
    returns a set of all the yields such that both passages have a unit with that yield.
    eval type can be:
    1. unlabeled: it doesn't matter what labels are there.
    2. labeled: also requires tag match (if there are multiple units with the same yield, requires one match)
    3. weak_labeled: also requires weak tag match (if there are multiple units with the same yield, requires one match)

    returns a 4-tuple:
    -- the set of mutual yields
    -- the set of mutual remote yields (unless separate_remotes is False, then None)
    -- the set of yields of passage1
    -- the set of yields of passage2
    """
    def _find_mutuals(m1, m2):
        mutual_ys = set()
        error_counter = Counter()

        for y in m1.keys():
            if y in m2.keys():
                if eval_type == "unlabeled":
                    mutual_ys.add(y)
                else:
                    tags1 = set(e.tag for e in m1[y])
                    tags2 = set(e.tag for e in m2[y])
                    if eval_type == "weak_labeled":
                        tags1 = expand_equivalents(tags1)
                    if tags1 & tags2:  # non-empty intersection
                        mutual_ys.add(y)
                    else:
                        error_counter[(str(tags1), str(tags2))] += 1
                        if ('E' in tags1 and 'C' in tags2) or \
                           ('C' in tags1 and 'E' in tags2):
                            print('C-E', to_text(passage1, y))
                        elif ('P' in tags1 and 'C' in tags2) or \
                             ('C' in tags1 and {'P', 'S'} & tags2):
                            print('P|S-C', to_text(passage1, y))
                        elif ('A' in tags1 and 'E' in tags2) or \
                             ('E' in tags1 and 'A' in tags2):
                            print('A-E', to_text(passage1, y))

        return mutual_ys, error_counter
    
    map1, map1_remotes = create_passage_yields(passage1, not separate_remotes)
    map2, map2_remotes = create_passage_yields(passage2, not separate_remotes)
    
    output, errors = _find_mutuals(map1, map2)
    output_remotes = None
    if separate_remotes:
        output_remotes, _ = _find_mutuals(map1_remotes, map2_remotes)
    
    return (output, set(map1.keys()), set(map2.keys()),
            output_remotes, set(map1_remotes.keys()), set(map2_remotes.keys()),
            errors)


def create_passage_yields(p, remote_terminals=False):
    """
    returns two dicts:
    1. maps a set of terminal indices (excluding punctuation) to a list of layer1 edges whose yield (excluding remotes
       and punctuation) is that set.
    2. maps a set of terminal indices (excluding punctuation) to a set of remote edges whose yield (excluding remotes
       and punctuation) is that set.
    remoteTerminals - if true, regular table includes remotes.
    """
    l1 = p.layer("1")
    edges = []
    for node in l1.all:
        edges.extend([e for e in node if e.tag not in ('U', 'LA', 'LR', 'T')])
   
    table_reg, table_remote = dict(), dict()
    for e in edges:
        pos = frozenset(t.position for t in e.child.get_terminals(punct=False, remotes=remote_terminals))
        if e.attrib.get("remote"):
            table_remote[pos] = table_remote.get(pos, []) + [e]
        else:
            table_reg[pos] = table_reg.get(pos, []) + [e]

    return table_reg, table_remote


def expand_equivalents(tag_set):
    """Returns a set of all the tags in the tag set or those equivalent to them"""
    output = tag_set.copy()
    for t in tag_set:
        for pair in EQUIV:
            if t in pair:
                output.update(pair)
    return output


def tag_distribution(unit_list):
    """Given a list of units, it returns a dict which maps the tags of the units to their frequency in the text"""
    output = Counter()
    for u in unit_list:
        output[u.tag] += 1
    return output


#######################################################################################
# Returns the command line parser.
#######################################################################################
def cmd_line_parser():
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("--db", "-d", dest="db_filename", action="store", type="string",
                      help="the db file name")
    parser.add_option("--pid", "-p", dest="pid", action="store", type="int",
                      help="the passage ID")
    parser.add_option("--from_xids", "-x", dest="from_xids", action="store_true",
                      help="interpret the ref and the guessed parameters as Xids in the db")
    parser.add_option("--guessed", "-g", dest="guessed", action="store", type="string",
                      help="if a db is defined - the username for the guessed annotation; else - the xml file name"
                           " for the guessed annotation")
    parser.add_option("--ref", "-r", dest="ref", action="store", type="string",
                      help="if a db is defined - the username for the reference annotation; else - the xml file"
                           " name for the reference annotation")
    parser.add_option("--units", "-u", dest="units", action="store_true",
                      help="the units the annotations have in common, and those each has separately")
    parser.add_option("--fscore", "-f", dest="fscore", action="store_true",
                      help="outputs the traditional P,R,F instead of the scene structure evaluation")
    parser.add_option("--debug", dest="debug", action="store_true",
                      help="run in debug mode")
    parser.add_option("--reference_from_file", dest="ref_from_file", action="store_true",
                      help="loads the reference from a file and not from the db")
    parser.add_option("--errors", "-e", dest="errors", action="store_true",
                      help="prints the error distribution according to its frequency")
    return parser


def get_text(p, positions):
    return [p.layer("0").by_position(pos).text for pos in positions
            if 0 < pos <= len(p.layer("0").all)]


def get_scores(p1, p2, eval_type):
    """
    prints the relevant statistics and f-scores. eval_type can be 'unlabeled', 'labeled' or 'weak_labeled'.
    """
    def _print_scores(num_matches, num_only_guessed, num_only_ref):
        """Prints the F scores according to the given numbers."""
        num_guessed = num_matches + num_only_guessed
        num_ref = num_matches + num_only_ref
        p = "NaN" if num_guessed == 0 else 1.0 * num_matches / num_guessed
        r = "NaN" if num_ref == 0 else 1.0 * num_matches / num_ref
        f = "NaN" if "NaN" in (p, r) else 0.0 if (p, r) == (0, 0) else 2 * p * r / float(p + r)

        print("Precision: {:.3} ({}/{})".format(p, num_matches, num_guessed))
        print("Recall: {:.3} ({}/{})".format(r, num_matches, num_ref))
        print("F1: {:.3}".format(f))

    mutual, all1, all2, mutual_rem, all1_rem, all2_rem, err_counter = mutual_yields(p1, p2, eval_type)
    print("Evaluation type: (" + eval_type + ")")
    
    if options.units:
        print("==> Mutual Units:")
        for y in mutual:
            print(get_text(p1, y))

        print("==> Only in guessed:")
        for y in all1 - mutual:
            print(get_text(p1, y))

        print("==> Only in reference:")
        for y in all2 - mutual:
            print(get_text(p1, y))

    if options.fscore:
        print("\nRegular Edges:")
        _print_scores(len(mutual), len(all1 - mutual), len(all2 - mutual))

        print("\nRemote Edges:")
        _print_scores(len(mutual_rem), len(all1_rem - mutual_rem), len(all2_rem - mutual_rem))
        print()

    if options.errors:
        print("\nConfusion Matrix:\n")
        for error, freq in err_counter.most_common():
            print(error[0], '\t', error[1], '\t', freq)
            
def evaluate_and_print(guess_passage, gold_passage):
    options = type('Options', (object,), { "units": true, "fscore": True, "errors": True })
    for passage in (guess_passage, gold_passage):
        flatten_centers(passage)  # flatten Cs inside Cs

    for evaluation_type in "labeled", "unlabeled", "weak_labeled":
        get_scores(passages[0], passages[1], evaluation_type)

################
# MAIN         #
################

if __name__ == "__main__":
    opt_parser = cmd_line_parser()
    (options, args) = opt_parser.parse_args()
    if len(args) > 0:
        opt_parser.error("all arguments must be flagged")

    if options.guessed is None or options.ref is None:
        opt_parser.error("missing arguments. type --help for help.")
    if options.pid is not None and options.from_xids is not None:
        opt_parser.error("inconsistent parameters. you can't have both a pid and from_xids paramters.")

    # if options.db_filename is None:
        # Read the xmls from files
    xmls = []
    files = [options.guessed, options.ref]
    for filename in files:
        in_file = open(filename)
        xmls.append(ElementTree().parse(in_file))
        in_file.close()
    # elif options.ref_from_file:
    #     xmls = ucca_db.get_xml_trees(options.db_filename, options.pid, [options.guessed])
    #     in_file = open(options.ref)
    #     xmls.append(ElementTree().parse(in_file))
    #     in_file.close()
    # else:
    #     keys = [options.guessed, options.ref]
    #     if options.from_xids:
    #         xmls = ucca_db.get_by_xids(options.db_filename, keys)
    #     else:
    #         xmls = ucca_db.get_xml_trees(options.db_filename, options.pid, keys)

    passages = [convert.from_standard(x) for x in xmls]

    for passage in passages:
        flatten_centers(passage)  # flatten Cs inside Cs

    if options.units or options.fscore or options.errors:
        for evaluation_type in "labeled", "unlabeled", "weak_labeled":
            get_scores(passages[0], passages[1], evaluation_type)
    #else:
    #    scene_structures = [layer1s.SceneStructure(x) for x in passages]
    #    comp = comparison.PassageComparison(scene_structures[0], scene_structures[1])
    #    comp.text_report(sys.stdout)
