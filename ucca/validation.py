from ucca import layer0, layer1
from ucca.layer0 import NodeTags as L0Tags
from ucca.layer1 import EdgeTags as ETags, NodeTags as L1Tags

LINKAGE = (ETags.LinkArgument, ETags.LinkRelation)


def validate(passage):
    for node in passage.layer(layer0.LAYER_ID).all:
        if not node.incoming:
            yield "Orphan %s terminal (%s) '%s'" % (node.tag, node.ID, node)
        elif len(node.incoming) > 1:
            yield "Reentrant %s terminal (%s) '%s'" % (node.tag, join(node.incoming), node)
    stack = [list(passage.layer(layer1.LAYER_ID).heads)]
    for node in stack[-1]:
        if node.ID != "1.1" and node.tag != L1Tags.Linkage:
            yield "Extra root (%s)" % node.ID
        terminals = [n for n in node.children if n.layer.ID == layer0.LAYER_ID]
        if terminals:
            yield "Terminal children (%s) of root (%s)" % (join(terminals), node)
        for edge in node:
            if edge.tag not in (ETags.ParallelScene, ETags.Linker, ETags.Function, ETags.Ground, ETags.Punctuation,
                                ETags.LinkRelation, ETags.LinkArgument):
                yield "Top-level %s edge (%s)" % (edge.tag, edge)
    visited = set()
    path = []
    path_set = set(path)
    while stack:
        for node in stack[-1]:
            if node in path_set:
                yield "Detected cycle (%s)" % "->".join(n.ID for n in path)
            elif node not in visited:
                visited.add(node)
                path.append(node)
                path_set.add(node)
                stack.append(node.children)
                incoming = tag_to_edge(node.incoming)
                outgoing = tag_to_edge(node)
                incoming_tags = set(incoming)
                outgoing_tags = set(outgoing)
                if node.tag == L1Tags.Linkage:
                    if node.incoming:
                        yield "Non-root %s node (%s)" % (node.tag, node)
                    s = outgoing_tags.difference(LINKAGE)
                    if s:
                        yield "%s node (%s) with %s children" % (node.tag, node, join(s))
                    if ETags.LinkRelation not in outgoing:
                        yield "%s node without %s child" % (node.tag, ETags.LinkRelation)
                elif node.tag == L1Tags.Foundational:
                    if node.participants and not node.is_scene():
                        yield "Node (%s) with participants but without main relation" % node.ID
                    if node.process and node.state:
                        yield "Node (%s) with both process (%s) and state (%s)" % (node.ID, node.process, node.state)
                    if node.parallel_scenes:
                        s = outgoing_tags.difference((ETags.ParallelScene, ETags.Punctuation, ETags.Linker,
                                                           ETags.Ground, ETags.Relator, ETags.Function))
                        if s:
                            yield "Node (%s) with parallel scenes has %s edge" % (node.ID, join(s))
                    s = outgoing_tags.intersection(LINKAGE)
                    if s:
                        yield "Non-linkage node (%s) with %s edges" % (node, join(s))
                primary_incoming = [e for e in node.incoming if not e.attrib.get("remote") and e.tag not in LINKAGE]
                if len(primary_incoming) > 1:
                    yield "Multiple incoming non-remote (%s)" % join(primary_incoming)
                for edge in node:
                    if (edge.tag == ETags.Punctuation) != (edge.child.tag == L1Tags.Punctuation):
                        yield "%s edge (%s) with %s child" % (edge.tag, edge, edge.child.tag)
                    if (node.tag == L1Tags.Punctuation) != (edge.child.tag == L0Tags.Punct):
                        yield "%s node (%s) with %s child (%s)" % (node.tag, node.ID, edge.child.tag, edge.child.ID)
                if node.attrib.get("implicit") and node.outgoing:
                    yield "Implicit node (%s) with outgoing edges (%s)" % (node.ID, join(node))
                for tag in (ETags.Function, ETags.Ground, ETags.ParallelScene, ETags.Linker, ETags.LinkRelation,
                                   ETags.Connector, ETags.Punctuation, ETags.Terminal):
                    s = incoming.get(tag, ())
                    if len(s) > 1:
                        yield "Multiple incoming %s edges (%s)" % (tag, join(s))
                for tag in (ETags.LinkRelation, ETags.Process, ETags.State):
                    s = outgoing.get(tag, ())
                    if len(s) > 1:
                        yield "Multiple outgoing %s edges (%s)" % (tag, join(s))
                if ETags.Function in incoming:
                    s = outgoing_tags.difference(ETags.Terminal, ETags.Punctuation)
                    if s:
                        yield "%s node (%s) with outgoing %s edge" % (ETags.Function, node.ID, join(s))
                if ETags.Linker in incoming_tags:
                    s = incoming_tags.difference((ETags.Linker, ETags.LinkRelation))
                    if s:
                        yield "%s node (%s) with incoming %s edge" % (ETags.Linker, node.ID, join(s))
                    if ETags.LinkRelation not in incoming_tags:
                        yield "%s node (%s) with no incoming %s" % (ETags.Linker, node.ID, ETags.LinkRelation)
                break
        else:
            if path:
                path_set.remove(path.pop())
            stack.pop()


def tag_to_edge(edges):
    d = {}
    for edge in edges:
        d.setdefault(edge.tag, []).append(edge)
    return d


def join(items):
    return ", ".join(map(str, items))
