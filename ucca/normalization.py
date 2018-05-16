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


def move_relators(node, l0):
    if node.is_scene():
        for edge in node:
            if edge.tag == layer1.EdgeTags.Relator:
                terminals = sorted(edge.child.get_terminals(), key=attrgetter("position"))
                parent = highest_ancestor(by_position(l0, terminals[-1].position + 1),
                                          *filter(None, (node.process, node.state)))
                if parent:
                    parent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
                    node.remove(edge)


def separate_scenes(node, l1):
    if (node.is_scene() or node.participants) and node.parallel_scenes:
        scene = l1.add_fnode(node, layer1.EdgeTags.ParallelScene)
        for edge in node:
            if edge.tag not in (layer1.EdgeTags.ParallelScene, layer1.EdgeTags.Punctuation, layer1.EdgeTags.Linker,
                                layer1.EdgeTags.Ground):
                scene.add(edge.tag, edge.child, edge_attrib=edge.attrib)
                node.remove(edge)


def highest_ancestor(included, *excluded):
    parents = [included] if included else []
    while parents:
        node = parents.pop(0)
        for edge in node.incoming:
            if not edge.attrib.get("remote") and edge.parent.tag == layer1.NodeTags.Foundational:
                if node.tag == layer1.NodeTags.Foundational and not node.terminals and \
                        any(n in edge.parent.iter() for n in excluded):
                    return node
                parents.append(edge.parent)
    return None


def lowest_common_ancestor(*nodes):
    parents = [nodes[0]] if nodes else []
    while parents:
        for parent in parents:
            if parent.tag == layer1.NodeTags.Foundational and not parent.terminals \
                    and all(n in parent.iter() for n in nodes[1:]):
                return parent
        parents = [p for n in parents for p in n.parents]
    return None


def by_position(l0, position):
    try:
        return l0.by_position(position)
    except IndexError:
        return None


def punct_parent(l0, *terminals):
    return lowest_common_ancestor(*filter(lambda n: n is not None and n.tag == layer0.NodeTags.Word,
                                          (by_position(l0, terminals[0].position - 1),
                                           by_position(l0, terminals[-1].position + 1))))


def attach_punct(l0, l1):
    for node in l1.all:
        if node.tag == layer1.NodeTags.Punctuation:
            node.destroy()
    for terminal in l0.all:
        if layer0.is_punct(terminal) and not terminal.incoming:
            l1.add_punct(punct_parent(l0, terminal), terminal)


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
            move_relators(node, l0)
            separate_scenes(node, l1)
        flatten_centers(node)
    attach_punct(l0, l1)
