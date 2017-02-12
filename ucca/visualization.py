import operator
import warnings
from collections import defaultdict

import matplotlib.cbook
import networkx as nx

from ucca import layer0, layer1

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
warnings.filterwarnings("ignore", category=UserWarning)


def draw(passage):
    G = nx.DiGraph()
    terminals = sorted(passage.layer(layer0.LAYER_ID).all, key=operator.attrgetter("position"))
    G.add_nodes_from([(n.ID, {"t": n.text, "c": "white"}) for n in terminals])
    G.add_nodes_from([n.ID for n in passage.layer(layer1.LAYER_ID).all])
    G.add_edges_from([(n.ID, e.child.ID, {"l": e.tag}) for layer in passage.layers for n in layer.all for e in n])
    pos = topological_layout(passage)
    nx.draw(G, pos, arrows=False, linewidths=0, node_color=[d.get("c", "black") for n, d in G.nodes(data=True)])
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): d["l"] for u, v, d in G.edges(data=True)}, font_size=8)
    nx.draw_networkx_labels(G, pos, labels={n: d.get("t", "") for n, d in G.nodes(data=True)}, font_size=10)


def topological_layout(passage):
    visited = defaultdict(set)
    pos = {}
    remaining = [n for layer in passage.layers for n in layer.all if not n.parents]
    while remaining:
        node = remaining.pop()
        if node.ID in pos:  # done already
            continue
        if node.children:
            children = [c for c in node.children if c.ID not in pos and c not in visited[node.ID]]
            if children:
                visited[node.ID].update(children)  # to avoid cycles
                remaining += [node] + children
                continue
            xs, ys = zip(*(pos[c.ID] for c in node.children))
            pos[node.ID] = (sum(xs) / len(xs), 1 + max(ys))  # done with children
        else:  # leaf
            pos[node.ID] = (int(node.position), 0)
    return pos
