from operator import attrgetter

from ucca import layer0, layer1


def replace_center(edge):
    if len(edge.parent) == 1 and not edge.parent.parents:
        return layer1.EdgeTags.ParallelScene
    if edge.parent.participants and not edge.parent.is_scene():
        return layer1.EdgeTags.Process
    return edge.tag


def replace_edge_tags(node):
    for edge in node:
        if not edge.attrib.get("remote") and edge.tag == layer1.EdgeTags.Center:
            edge.tag = replace_center(edge)


def lower_common_ancestor(*nodes):
    parents = [nodes[0]]
    while parents:
        for parent in parents:
            if parent.tag == layer1.NodeTags.Foundational and all(n in parent.iter() for n in nodes[1:]):
                return parent
        parents = [p for n in parents for p in n.parents]
    return None


def by_position(l0, position):
    try:
        return l0.by_position(position)
    except IndexError:
        return None


def move_punctuation(node, l0):
    for edge in node:
        if edge.child.tag == layer1.NodeTags.Punctuation:
            terminals = sorted(edge.child.children, key=attrgetter("position"))
            parent = lower_common_ancestor(*filter(None, (by_position(l0, terminals[0].position - 1),
                                                          by_position(l0, terminals[-1].position + 1))))
            parent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
            node.remove(edge)


def flatten_centers(node):
    """
    Whenever there are Cs inside Cs, remove the external C.
    """
    if node.tag == layer1.NodeTags.Foundational and node.ftag == layer1.EdgeTags.Center and \
            len(node.centers) == len(node.fparent.centers) == 1:
        for edge in node.incoming:
            if edge.attrib.get("remote"):
                edge.parent.add(edge.tag, node.centers[0], edge_attrib=edge.attrib)
        for edge in node.outgoing:
            node.fparent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
        node.destroy()


def normalize(passage, extra=False):
    l0 = passage.layer(layer0.LAYER_ID)
    l1 = passage.layer(layer1.LAYER_ID)
    for node in l1.all:
        if extra:
            replace_edge_tags(node)
        move_punctuation(node, l0)
        flatten_centers(node)
