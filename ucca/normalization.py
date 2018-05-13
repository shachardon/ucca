from operator import attrgetter

from ucca import layer0, layer1


def lower_common_ancestor(*nodes):
    parents = [nodes[0]]
    while parents:
        for parent in parents:
            if parent.tag == layer1.NodeTags.Foundational and all(n in parent.iter() for n in nodes[1:]):
                return parent
        parents = [p for n in parents for p in n.parents]
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
                parent.add(edge.tag, edge.child)
                node.remove(edge)


def by_position(l0, position):
    try:
        return l0.by_position(position)
    except IndexError:
        return None
