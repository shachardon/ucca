from ucca import layer0, layer1
from ucca.layer0 import NodeTags as L0Tags
from ucca.layer1 import EdgeTags as ETags, NodeTags as L1Tags


def replace_center(edge):
    if len(edge.parent) == 1 and not edge.parent.parents:
        return ETags.ParallelScene
    if edge.parent.participants and not edge.parent.is_scene():
        return ETags.Process
    return edge.tag


def replace_edge_tags(node):
    for edge in node:
        if not edge.attrib.get("remote") and edge.tag == ETags.Center:
            edge.tag = replace_center(edge)


def move_elements(node, tags, parent_tags, forward=True):
    for edge in node:
        if edge.child.tag == L1Tags.Foundational and edge.tag in ((tags,) if isinstance(tags, str) else tags):
            try:
                parent_edge = min((e for e in node if e != edge and e.child.tag == L1Tags.Foundational),
                                  key=lambda e: abs(((edge.child.start_position - e.child.end_position),
                                                     (e.child.start_position - edge.child.end_position))[forward]))
            except ValueError:
                continue
            if parent_edge.tag in ((parent_tags,) if isinstance(parent_tags, str) else parent_tags):
                parent = parent_edge.child
                parent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
                node.remove(edge)


def move_scene_elements(node):
    if node.parallel_scenes:
        move_elements(node, tags=(ETags.Relator, ETags.Elaborator, ETags.Center), parent_tags=ETags.ParallelScene)


def move_sub_scene_elements(node):
    if node.is_scene():
        move_elements(node, tags=(ETags.Elaborator, ETags.Center), parent_tags=ETags.Participant, forward=False)


def separate_scenes(node, l1, top_level=False):
    if (node.is_scene() or node.participants) and (top_level or node.parallel_scenes):
        edges = list(node)
        scene = l1.add_fnode(node, ETags.ParallelScene)
        for edge in edges:
            if edge.tag not in (ETags.ParallelScene, ETags.Punctuation, ETags.Linker, ETags.Ground):
                scene.add(edge.tag, edge.child, edge_attrib=edge.attrib)
                node.remove(edge)


def lowest_common_ancestor(*nodes):
    parents = [nodes[0]] if nodes else []
    while parents:
        for parent in parents:
            if parent.tag == L1Tags.Foundational and not parent.terminals \
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
    return lowest_common_ancestor(*filter(lambda n: n is not None and n.tag == L0Tags.Word,
                                          (by_position(l0, terminals[0].position - 1),
                                           by_position(l0, terminals[-1].position + 1))))


def attach_punct(l0, l1):
    for node in l1.all:
        if node.tag == L1Tags.Punctuation:
            node.destroy()
    for terminal in l0.all:
        if layer0.is_punct(terminal) and not terminal.incoming:
            l1.add_punct(punct_parent(l0, terminal), terminal)


def flatten_centers(node):
    """
    Whenever there are Cs inside Cs, remove the external C.
    """
    if node.tag == L1Tags.Foundational and node.ftag == ETags.Center and \
            len(node.centers) == len(node.fparent.centers) == 1:
        for edge in node.incoming:
            if edge.attrib.get("remote"):
                edge.parent.add(edge.tag, node.centers[0], edge_attrib=edge.attrib)
        for edge in node.outgoing:
            node.fparent.add(edge.tag, edge.child, edge_attrib=edge.attrib)
        node.destroy()


def normalize_node(node, l1, extra):
    if node.tag == L1Tags.Foundational:
        if extra:
            replace_edge_tags(node)
            move_scene_elements(node)
            move_sub_scene_elements(node)
        separate_scenes(node, l1, top_level=node in l1.heads)
        flatten_centers(node)


def normalize(passage, extra=False):
    l0 = passage.layer(layer0.LAYER_ID)
    l1 = passage.layer(layer1.LAYER_ID)
    heads = list(l1.heads)
    stack = [heads]
    visited = set()
    path = []
    path_set = set(path)
    while stack:
        for node in stack[-1]:
            if node in path_set:
                try:
                    node.fparent.remove(node)
                except AttributeError:
                    pass
            elif node not in visited:
                visited.add(node)
                path.append(node)
                path_set.add(node)
                stack.append(node.children)
                normalize_node(node, l1, extra)
                break
        else:
            if path:
                path_set.remove(path.pop())
            stack.pop()
    attach_punct(l0, l1)
