def diff_passages(true_passage, pred_passage):
    """
    Debug method to print missing or mistaken attributes, nodes and edges
    """
    lines = list()
    if not true_passage._attrib.equals(pred_passage._attrib):
        lines.append("Passage attributes mismatch: %s, %s" %
                     (true_passage._attrib, pred_passage._attrib))
    try:
        for lid, l1 in true_passage._layers.items():
            l2 = true_passage.layer(lid)
            if not l1._attrib.equals(l2._attrib):
                lines.append("Layer %d attributes mismatch: %s, %s" %
                             (lid, l1._attrib, l2._attrib))
    except KeyError:  # no layer with same ID found
        lines.append("Missing layer: %s, %s" %
                     (true_passage._layers, pred_passage._layers))
    pred_ids = {node.extra["remarks"]: node
                for node in pred_passage.missing_nodes(true_passage)}
    true_ids = {node.ID: node
                for node in true_passage.missing_nodes(pred_passage)}
    for pred_id, pred_node in list(pred_ids.items()):
        true_node = true_ids.get(pred_id)
        if true_node:
            pred_ids.pop(pred_id)
            true_ids.pop(pred_id)
            pred_edges = {edge.tag + "->" + edge.child.ID: edge for edge in
                          pred_node.missing_edges(true_node)}
            true_edges = {edge.tag + "->" + edge.child.ID: edge for edge in
                          true_node.missing_edges(pred_node)}
            intersection = set(pred_edges).intersection(set(true_edges))
            pred_edges = {s: edge for s, edge in pred_edges.items() if s not in intersection}
            true_edges = {s: edge for s, edge in true_edges.items() if s not in intersection}
            if pred_edges or true_edges:
                lines.append("For node " + pred_id + ":")
                if pred_edges:
                    lines.append("  Mistake edges: %s" % ", ".join(pred_edges))
                if true_edges:
                    lines.append("  Missing edges: %s" % ", ".join(true_edges))
    if pred_ids:
        lines.append("Mistake nodes: %s" % ", ".join(pred_ids))
    if true_ids:
        lines.append("Missing nodes: %s" % ", ".join(true_ids))
    return "\n".join(lines)