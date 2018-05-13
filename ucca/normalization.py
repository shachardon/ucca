from operator import attrgetter

from ucca import layer0, layer1


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


def normalize(passage):
    l0 = passage.layer(layer0.LAYER_ID)
    l1 = passage.layer(layer1.LAYER_ID)
    for node in l1.all:
        for edge in node:
            if edge.child.tag == layer1.NodeTags.Punctuation:
                terminals = sorted(edge.child.children, key=attrgetter("position"))
                parent = lower_common_ancestor(*filter(None, (by_position(l0, terminals[0].position - 1),
                                                              by_position(l0, terminals[-1].position + 1))))
                parent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
                node.remove(edge)
        flatten_centers(node)
