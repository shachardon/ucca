import string

from ucca import layer0, layer1
from ucca.layer0 import NodeTags as L0Tags
from ucca.layer1 import EdgeTags as ETags, NodeTags as L1Tags

LINKAGE = (ETags.LinkArgument, ETags.LinkRelation)


def validate(passage, linkage=True):
    for node in passage.layer(layer0.LAYER_ID).all:
        yield from NodeValidator(node).validate_terminal()
    heads = list(passage.layer(layer1.LAYER_ID).heads)
    found_linkage = False
    for node in heads:
        if node.tag == L1Tags.Linkage:
            found_linkage = True
        yield from NodeValidator(node).validate_top_level()
    stack = [heads]
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
                yield from NodeValidator(node).validate_non_terminal(linkage=linkage and found_linkage)
                break
        else:
            if path:
                path_set.remove(path.pop())
            stack.pop()


class NodeValidator:
    def __init__(self, node):
        self.node = node
        self.incoming = tag_to_edge(node.incoming)
        self.outgoing = tag_to_edge(node)
        self.incoming_tags = set(self.incoming)
        self.outgoing_tags = set(self.outgoing)

    def validate_terminal(self):
        if not self.node.text:
            yield "Empty terminal text (%s)" % self.node.ID
        if set(self.node.text).intersection(string.whitespace):
            yield "Whitespace in terminal text (%s): '%s'" % (self.node.ID, self.node)
        if not self.incoming:
            yield "Orphan %s terminal (%s) '%s'" % (self.node.tag, self.node.ID, self.node)
        elif len(self.node.incoming) > 1:
            yield "Reentrant %s terminal (%s) '%s'" % (self.node.tag, join(self.node.incoming), self.node)

    def validate_top_level(self):
        if self.node.ID != "1.1" and self.node.tag != L1Tags.Linkage:
            yield "Extra root (%s)" % self.node.ID
        terminals = [n for n in self.node.children if n.layer.ID == layer0.LAYER_ID]
        if terminals:
            yield "Terminal children (%s) of root (%s)" % (join(terminals), self.node)
        s = self.outgoing_tags.difference((ETags.ParallelScene, ETags.Linker, ETags.Function, ETags.Ground,
                                           ETags.Punctuation, ETags.LinkRelation, ETags.LinkArgument))
        if s:
            yield "Top-level node (%s) with %s edge" % (self.node.ID, join(s))

    def validate_non_terminal(self, linkage=False):
        if linkage and self.node.tag == L1Tags.Linkage:
            yield from self.validate_linkage()
        elif self.node.tag == L1Tags.Foundational:
            yield from self.validate_foundational()
        primary_incoming = [e for e in self.node.incoming if not e.attrib.get("remote") and e.tag not in LINKAGE]
        if len(primary_incoming) > 1:
            yield "Multiple incoming non-remote (%s)" % join(primary_incoming)
        remote_incoming = [e for e in self.node.incoming if e.attrib.get("remote")]
        if remote_incoming and not primary_incoming:
            yield "Node (%s) with remote parents but no primary parents" % self.node.ID
        for edge in self.node:
            if (edge.tag == ETags.Punctuation) != (edge.child.tag == L1Tags.Punctuation):
                yield "%s edge (%s) with %s child" % (edge.tag, edge, edge.child.tag)
            # FN parent of Punctuation is disallowed unless the FN is unanalyzable
            if (self.node.tag == L1Tags.Foundational) and (edge.child.tag == L0Tags.Punct) and \
                    not len(self.node.terminals) + len(self.node.punctuation) == len(self.node.children) > 1 or \
                    (self.node.tag == L1Tags.Punctuation) and not (edge.child.tag == L0Tags.Punct):
                yield "%s node (%s) with %s child (%s)" % (self.node.tag, self.node.ID, edge.child.tag, edge.child.ID)
        if self.node.attrib.get("implicit"):
            if self.node.outgoing:
                yield "Implicit node (%s) with outgoing edges (%s)" % (self.node.ID, join(self.node))
        elif self.node.tag in (L1Tags.Foundational, L1Tags.Linkage, L1Tags.Punctuation) and \
                all(e.attrib.get("remote") for e in self.node):
            yield "Non-implicit node (%s) with no primary children" % (self.node.ID)
        for tag in (ETags.Function, ETags.ParallelScene, ETags.Linker, ETags.LinkRelation,
                    ETags.Connector, ETags.Punctuation, ETags.Terminal):
            s = self.incoming.get(tag, ())
            if len(s) > 1:
                yield "Multiple incoming %s edges (%s)" % (tag, join(s))
        for tag in (ETags.LinkRelation, ETags.Process, ETags.State):
            s = self.outgoing.get(tag, ())
            if len(s) > 1:
                yield "Multiple outgoing %s edges (%s)" % (tag, join(s))
        if ETags.Function in self.incoming:
            s = self.outgoing_tags.difference((ETags.Terminal, ETags.Punctuation))
            if s:
                yield "%s node (%s) with outgoing %s edge: %s" % (ETags.Function, self.node.ID, join(s), self.node)
        if ETags.Linker in self.incoming_tags and linkage and ETags.LinkRelation not in self.incoming_tags:
            yield "%s node (%s) with no incoming %s" % (ETags.Linker, self.node.ID, ETags.LinkRelation)

    def validate_linkage(self):
        if self.node.incoming:
            yield "Non-root %s node (%s)" % (self.node.tag, self.node)
        s = self.outgoing_tags.difference(LINKAGE)
        if s:
            yield "%s node (%s) with %s children" % (self.node.tag, self.node, join(s))
        if ETags.LinkRelation not in self.outgoing:
            yield "%s node without %s child" % (self.node.tag, ETags.LinkRelation)

    def validate_foundational(self):
        if self.node.participants and not self.node.is_scene():
            yield "Node (%s) with participants but without main relation: %s" % (self.node.ID, self.node)
        if self.node.process and self.node.state:
            yield "Node (%s) with both process (%s) and state (%s)" % (self.node.ID, self.node.process, self.node.state)
        if self.node.parallel_scenes:
            s = self.outgoing_tags.difference((ETags.ParallelScene, ETags.Punctuation, ETags.Linker,
                                               ETags.Ground, ETags.Relator, ETags.Function))
            if s:
                yield "Node (%s) with parallel scenes has %s edge" % (self.node.ID, join(s))
        s = self.outgoing_tags.intersection(LINKAGE)
        if s:
            yield "Non-linkage node (%s) with %s edges" % (self.node, join(s))


def tag_to_edge(edges):
    d = {}
    for edge in edges:
        d.setdefault(edge.tag, []).append(edge)
    return d


def join(items):
    return ", ".join(map(str, items))
