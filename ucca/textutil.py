"""Utility functions for UCCA package."""
from core import Passage
from layer0 import Layer0
from layer1 import Layer1
from ucca import layer0, layer1


SENTENCE_END_MARKS = ('.', '?', '!')


def break2sentences(passage):
    """Breaks paragraphs into sentences according to the annotation.

    A sentence is a list of terminals which ends with a mark from
    SENTENCE_END_MARKS, and is also the end of a paragraph or parallel scene.
    :param passage: the Passage object to operate on
    :return: a list of positions in the Passage, each denotes a closing Terminal
        of a sentence.
    """
    l1 = passage.layer(layer1.LAYER_ID)
    terminals = passage.layer(layer0.LAYER_ID).all
    ps_ends = [ps.end_position for ps in l1.top_scenes]
    ps_starts = [ps.start_position for ps in l1.top_scenes]
    marks = [t.position for t in terminals if t.text in SENTENCE_END_MARKS]
    # Annotations doesn't always include the ending period (or other mark)
    # with the parallel scene it closes. Hence, if the terminal before the
    # mark closed the parallel scene, and this mark doesn't open a scene
    # in any way (hence it probably just "hangs" there), it's a sentence end
    marks = [x for x in marks
             if x in ps_ends or ((x - 1) in ps_ends and x not in ps_starts)]
    return sorted(set(marks + break2paragraphs(passage)))


def break2paragraphs(passage):
    """Breaks into paragraphs according to the annotation.

    Uses the `paragraph' attribute of layer 0 to find paragraphs.
    :param passage: the Passage object to operate on
    :return: a list of positions in the Passage, each denotes a closing Terminal
        of a paragraph.
    """
    terminals = passage.layer(layer0.LAYER_ID).all
    paragraph_ends = [(t.position - 1) for t in terminals
                      if t.position != 1 and t.para_pos == 1]
    paragraph_ends.append(terminals[-1].position)
    return paragraph_ends


def split2sentences(passage, remarks=False):
    ends = break2sentences(passage)
    return split_passage(passage, ends, remarks=remarks)


def split2paragraphs(passage, remarks=False):
    ends = break2paragraphs(passage)
    return split_passage(passage, ends, remarks=remarks)


def split_passage(passage, ends, remarks=False):
    """
    Split the passage on the given terminal positions
    :param passage: passage to split
    :param ends: sequence of positions at which the split passages will end
    :return: sequence of passages
    :param remarks: add original node ID as remarks to the new nodes
    """
    passages = []
    for start, end in zip([0] + ends[:-1], ends):
        other = Passage(ID=passage.ID, attrib=passage.attrib.copy())
        other.extra = passage.extra.copy()
        # Create terminals and find layer 1 nodes to be included
        l0 = passage.layer(layer0.LAYER_ID)
        other_l0 = Layer0(root=other, attrib=l0.attrib.copy())
        other_l0.extra = l0.extra.copy()
        level = set()
        nodes = set()
        id_to_other = {}
        for terminal in l0.all[start:end]:
            other_terminal = other_l0.add_terminal(terminal.text, terminal.punct, terminal.paragraph)
            other_terminal.extra = terminal.extra.copy()
            if remarks:
                other_terminal.extra["remarks"] = terminal.ID
            id_to_other[terminal.ID] = other_terminal
            level.update(terminal.parents)
            nodes.add(terminal)
        while level:
            nodes.update(level)
            level = set(p for n in level for p in n.parents if p not in nodes)

        Layer1(root=other, attrib=passage.layer(layer1.LAYER_ID).attrib.copy())
        _copy_l1_nodes(passage, other, id_to_other, nodes, remarks=remarks)
        other.frozen = passage.frozen
        passages.append(other)
    return passages


def join_passages(passages, remarks=False):
    """
    Join passages to one passage with all the nodes in order
    :param passages: sequence of passages to join
    :param remarks: add original node ID as remarks to the new nodes
    :return: joined passage
    """
    other = Passage(ID=passages[0].ID, attrib=passages[0].attrib.copy())
    other.extra = passages[0].extra.copy()
    l0 = passages[0].layer(layer0.LAYER_ID)
    l1 = passages[0].layer(layer1.LAYER_ID)
    other_l0 = Layer0(root=other, attrib=l0.attrib.copy())
    Layer1(root=other, attrib=l1.attrib.copy())
    for passage in passages:
        id_to_other = {}
        l0 = passage.layer(layer0.LAYER_ID)
        for terminal in l0.all:
            other_terminal = other_l0.add_terminal(terminal.text, terminal.punct, terminal.paragraph)
            other_terminal.extra = terminal.extra.copy()
            if remarks:
                other_terminal.extra["remarks"] = terminal.ID
            id_to_other[terminal.ID] = other_terminal
        _copy_l1_nodes(passage, other, id_to_other, remarks=remarks)
    return other


def _copy_l1_nodes(passage, other, id_to_other, nodes=None, remarks=False):
    """
    Copy all layer 1 nodes from one passage to another
    :param passage: source passage
    :param other: target passage
    :param id_to_other: dictionary mapping IDs from passage to existing nodes from other
    :param nodes: if given, only the nodes from this set will be copied
    :param remarks: add original node ID as remarks to the new nodes
    """
    l1 = passage.layer(layer1.LAYER_ID)
    other_l1 = other.layer(layer1.LAYER_ID)
    queue = [(node, None) for node in l1.heads]
    linkages = []
    remotes = []
    while queue:
        node, other_node = queue.pop()
        if node.tag == layer1.NodeTags.Linkage and (
                        nodes is None or nodes.issuperset(node.children)):
            linkages.append(node)
            continue
        for edge in node.outgoing:
            child = edge.child
            if nodes is None or child in nodes or child.attrib.get("implicit"):
                if edge.attrib.get("remote"):
                    remotes.append((edge, other_node))
                    continue
                if child.layer.ID == layer0.LAYER_ID:
                    other_node.add(edge.tag, id_to_other[child.ID])
                    continue
                if child.tag == layer1.NodeTags.Punctuation:
                    grandchild = child.children[0]
                    other_child = other_l1.add_punct(other_node, id_to_other[grandchild.ID])
                    other_grandchild = other_child.children[0]
                    other_grandchild.extra = grandchild.extra.copy()
                    if remarks:
                        other_grandchild.extra["remarks"] = grandchild.ID
                else:
                    other_child = other_l1.add_fnode(other_node, edge.tag,
                                                     implicit=child.attrib.get("implicit"))
                    queue.append((child, other_child))

                id_to_other[child.ID] = other_child
                other_child.extra = child.extra.copy()
                if remarks:
                    other_child.extra["remarks"] = child.ID
    # Add remotes
    for edge, parent in remotes:
        other_l1.add_remote(parent, edge.tag, id_to_other[edge.child.ID])
    # Add linkages
    for linkage in linkages:
        other_linkage = other_l1.add_linkage(linkage.relation, *linkage.arguments)
        other_linkage.extra = linkage.extra.copy()
        if remarks:
            other_linkage.extra["remarks"] = linkage.ID
    for head, other_head in zip(l1.heads, other_l1.heads):
        other_head.extra = head.extra.copy()
        if remarks:
            other_head.extra["remarks"] = head.ID


def indent_xml(xml_as_string):
    """Indents a string of XML-like objects.

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
