import operator
import warnings
from collections import defaultdict

import matplotlib.cbook
import networkx as nx

from ucca import layer0, layer1
from ucca.layer1 import Linkage

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
warnings.filterwarnings("ignore", category=UserWarning)


def draw(passage):
    G = nx.DiGraph()
    terminals = sorted(passage.layer(layer0.LAYER_ID).all, key=operator.attrgetter("position"))
    G.add_nodes_from([(n.ID, {"label": n.text, "node_color": "white"}) for n in terminals])
    G.add_nodes_from([(n.ID, {"label": "IMPLICIT" if n.attrib.get("implicit") else "",
                              "node_color": "gray" if isinstance(n, Linkage) else (
                                  "white" if n.attrib.get("implicit") else "black")})
                      for n in passage.layer(layer1.LAYER_ID).all])
    G.add_edges_from([(n.ID, e.child.ID, {"label": e.tag, "style": "dashed" if e.attrib.get("remote") else "solid"})
                      for layer in passage.layers for n in layer.all for e in n])
    pos = topological_layout(passage)
    nx.draw(G, pos, arrows=False, font_size=10,
            node_color=[d["node_color"] for _, d in G.nodes(data=True)],
            labels={n: d["label"] for n, d in G.nodes(data=True) if d["label"]},
            style=[d["style"] for _, _, d in G.edges(data=True)])
    nx.draw_networkx_edge_labels(G, pos, font_size=8,
                                 edge_labels={(u, v): d["label"] for u, v, d in G.edges(data=True)})


def topological_layout(passage):
    visited = defaultdict(set)
    pos = {}
    implicit_offset = 1 + max((n.position for n in passage.layer(layer0.LAYER_ID).all), default=-1)
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
        elif node.layer.ID == layer0.LAYER_ID:  # terminal
            pos[node.ID] = (int(node.position), 0)
        else:  # implicit
            pos[node.ID] = (implicit_offset, 0)
            implicit_offset += 1
    return pos


def tikz(p, indent=None):
    # child {node (After) [word] {After} edge from parent node[above] {\scriptsize $L$}}
    # child {node (graduation) [circle] {}
    # {
    # child {node [word] {graduation} edge from parent node[left] {\scriptsize $P$}}
    # } edge from parent node[right] {\scriptsize $H$} }
    # child {node [word] {,} edge from parent node[below] {\scriptsize $U$}}
    # child {node (moved) [circle] {}
    # {
    # child {node (John) [word] {John} edge from parent node[left] {\scriptsize $A$}}
    # child {node [word] {moved} edge from parent node[left] {\scriptsize $P$}}
    # child {node [circle] {}
    # {
    # child {node [word] {to} edge from parent node[left] {\scriptsize $R$}}
    # child {node [word] {Paris} edge from parent node[right] {\scriptsize $C$}}
    # } edge from parent node[right] {\scriptsize $A$} }
    # } edge from parent node[right] {\scriptsize $H$} }
    # ;
    # \draw[dashed,->] (graduation) to node [auto] {\scriptsize $A$} (John);
    if indent is None:
        return r"""
\begin{tikzpicture}[->,level distance=26mm,
  level 1/.style={sibling distance=10cm},
  level 2/.style={sibling distance=7cm},
  level 3/.style={sibling distance=2cm},
  every circle node/.append style={fill=black}]
  \tikzstyle{word} = [font=\rmfamily,color=black]
  """ + "\\" + tikz(p.layer(layer1.LAYER_ID).heads[0], indent=1) + r"""
;
\end{tikzpicture}"""
    s = "node (" + p.ID.replace(".", "_") + ") "
    if p.terminals:
        s += "[word] {" + " ".join(t.text for t in p.terminals) + "} "
    else:
        s += ("\n" + indent * "  ").join(["[circle] {}", "{"] +
                                         ["child {" + tikz(e.child, indent + 1) +
                                          "edge from parent node[auto] {\scriptsize $" + e.tag + "$}}"
                                          for e in p.outgoing if not e.attrib.get("remote")]) + " }"
    return s
