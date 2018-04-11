from ucca import layer0, layer1


def validate(passage):
    visited = set()
    nodes = list(passage.layer(layer1.LAYER_ID).all)
    while nodes:
        node = nodes.pop(0)
        visited |= set(node)
        for edge in node:
            assert edge not in visited, "Detected cycle: %s" % edge
            assert (edge.tag == layer1.EdgeTags.Punctuation) == (edge.child.tag == layer1.NodeTags.Punctuation), \
                "%s edge to %s node" % (edge.tag, edge.child.tag)
            assert node.tag == layer1.NodeTags.Punctuation == edge.child.tag == layer0.NodeTags.Punct, \
                "%s parent for %s node" % (node.tag, edge.child.tag)
            nodes.append(edge.child)
