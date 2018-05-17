from ucca import layer1
from .conftest import create_passage, create_discontiguous

"""Tests layer1 module functionality and correctness."""


def test_creation(self):
    p = create_passage()
    head = p.layer("1").heads[0]
    self.assertSequenceEqual([x.tag for x in head], ["L", "H", "H", "U"])
    self.assertSequenceEqual([x.child.position for x in head.children[0]],
                             [1])
    self.assertSequenceEqual([x.tag for x in head.children[1]],
                             ["P", "A", "U", "A"])
    self.assertSequenceEqual([x.child.position
                              for x in head.children[1].children[0]],
                             [2, 3, 4, 5])
    self.assertSequenceEqual([x.child.position
                              for x in head.children[1].children[1]],
                             [6, 7, 8, 9])
    self.assertSequenceEqual([x.child.position
                              for x in head.children[1].children[2]],
                             [10])
    self.assertTrue(head.children[1][3].attrib.get("remote"))


def test_fnodes(self):
    p = create_passage()
    l0 = p.layer("0")
    l1 = p.layer("1")

    terms = l0.all
    head, lkg1, lkg2 = l1.heads
    link1, ps1, ps23, punct2 = head.children
    p1, a1, punct1 = [x.child for x in ps1 if not x.attrib.get("remote")]
    ps2, link2, ps3 = ps23.children
    a2, d2 = [x.child for x in ps2 if not x.attrib.get("remote")]
    p3, a3, a4 = ps3.children

    self.assertEqual(lkg1.relation, link1)
    self.assertSequenceEqual(lkg1.arguments, [ps1])
    self.assertIsNone(ps23.process)
    self.assertEqual(ps2.process, p1)
    self.assertSequenceEqual(ps1.participants, [a1, d2])
    self.assertSequenceEqual(ps3.participants, [a3, a4])

    self.assertSequenceEqual(ps1.get_terminals(), terms[1:10])
    self.assertSequenceEqual(ps1.get_terminals(punct=False, remotes=True),
                             terms[1:9] + terms[14:15])
    self.assertEqual(ps1.end_position, 10)
    self.assertEqual(ps2.start_position, 11)
    self.assertEqual(ps3.start_position, 17)
    self.assertEqual(a4.start_position, -1)
    self.assertEqual(ps23.to_text(), "11 12 13 14 15 16 17 18 19")

    self.assertEqual(ps1.fparent, head)
    self.assertEqual(link2.fparent, ps23)
    self.assertEqual(ps2.fparent, ps23)
    self.assertEqual(d2.fparent, ps2)


def test_layer1(self):
    p = create_passage()
    l1 = p.layer("1")

    head, lkg1, lkg2 = l1.heads
    link1, ps1, ps23, punct2 = head.children
    p1, a1, punct1 = [x.child for x in ps1 if not x.attrib.get("remote")]
    ps2, link2, ps3 = ps23.children

    self.assertSequenceEqual(l1.top_scenes, [ps1, ps2, ps3])
    self.assertSequenceEqual(l1.top_linkages, [lkg1, lkg2])

    # adding scene #23 to linkage #1, which makes it non top-level as
    # scene #23 isn't top level
    lkg1.add(layer1.EdgeTags.LinkArgument, ps23)
    self.assertSequenceEqual(l1.top_linkages, [lkg2])

    # adding process to scene #23, which makes it top level and discards
    # "top-levelness" from scenes #2 + #3
    l1.add_remote(ps23, layer1.EdgeTags.Process, p1)
    self.assertSequenceEqual(l1.top_scenes, [ps1, ps23])
    self.assertSequenceEqual(l1.top_linkages, [lkg1, lkg2])

    # Changing the process tag of scene #1 to A and back, validate that
    # top scenes are updates accordingly
    p_edge = [e for e in ps1 if e.tag == layer1.EdgeTags.Process][0]
    p_edge.tag = layer1.EdgeTags.Participant
    self.assertSequenceEqual(l1.top_scenes, [ps23])
    self.assertSequenceEqual(l1.top_linkages, [lkg2])
    p_edge.tag = layer1.EdgeTags.Process
    self.assertSequenceEqual(l1.top_scenes, [ps1, ps23])
    self.assertSequenceEqual(l1.top_linkages, [lkg1, lkg2])


def test_str(self):
    p = create_passage()
    self.assertSequenceEqual([str(x) for x in p.layer("1").heads],
                             ["[L 1] [H [P 2 3 4 5] [A 6 7 8 9] [U 10] "
                              "... [A* 15] ] [H [H [P* 2 3 4 5] [A 11 12 "
                              "13 14] [D 15] ] [L 16] [H [A IMPLICIT] [S "
                              "17 18] [A 19] ] ] [U 20] ",
                              "1.2-->1.3", "1.11-->1.8,1.12"])


def test_destroy(self):
    p = create_passage()
    l1 = p.layer("1")

    head, lkg1, lkg2 = l1.heads
    link1, ps1, ps23, punct2 = head.children
    p1, a1, punct1 = [x.child for x in ps1 if not x.attrib.get("remote")]
    ps2, link2, ps3 = ps23.children

    ps1.destroy()
    self.assertSequenceEqual(head.children, [link1, ps23, punct2])
    self.assertSequenceEqual(p1.parents, [ps2])
    self.assertFalse(a1.parents)
    self.assertFalse(punct1.parents)


def test_discontiguous(self):
    """Tests FNode.discontiguous and FNode.get_sequences"""
    p = create_discontiguous()
    l1 = p.layer("1")
    head = l1.heads[0]
    ps1, ps2, ps3 = head.children
    d1, a1, p1, f1 = ps1.children
    e1, c1, e2, g1 = d1.children
    d2, g2, p2, a2 = ps2.children
    t14, p3, a3 = ps3.children

    # Checking discontiguous property
    self.assertFalse(ps1.discontiguous)
    self.assertFalse(d1.discontiguous)
    self.assertFalse(e1.discontiguous)
    self.assertFalse(e2.discontiguous)
    self.assertTrue(c1.discontiguous)
    self.assertTrue(g1.discontiguous)
    self.assertTrue(a1.discontiguous)
    self.assertTrue(p1.discontiguous)
    self.assertFalse(f1.discontiguous)
    self.assertTrue(ps2.discontiguous)
    self.assertFalse(p2.discontiguous)
    self.assertFalse(a2.discontiguous)
    self.assertFalse(ps3.discontiguous)
    self.assertFalse(a3.discontiguous)

    # Checking get_sequences -- should return only non-remote, non-implicit
    # stretches of terminals
    self.assertSequenceEqual(ps1.get_sequences(), [(1, 10)])
    self.assertSequenceEqual(d1.get_sequences(), [(1, 4)])
    self.assertSequenceEqual(e1.get_sequences(), [(1, 1)])
    self.assertSequenceEqual(e2.get_sequences(), [(3, 3)])
    self.assertSequenceEqual(c1.get_sequences(), [(2, 2), (4, 4)])
    self.assertSequenceEqual(a1.get_sequences(), [(5, 5), (8, 8)])
    self.assertSequenceEqual(p1.get_sequences(), [(6, 7), (10, 10)])
    self.assertSequenceEqual(f1.get_sequences(), [(9, 9)])
    self.assertSequenceEqual(ps2.get_sequences(), [(11, 14), (18, 20)])
    self.assertSequenceEqual(p2.get_sequences(), [(11, 14)])
    self.assertSequenceEqual(a2.get_sequences(), [(18, 20)])
    self.assertSequenceEqual(d2.get_sequences(), ())
    self.assertSequenceEqual(g2.get_sequences(), ())
    self.assertSequenceEqual(ps3.get_sequences(), [(15, 17)])
    self.assertSequenceEqual(a3.get_sequences(), [(16, 17)])
    self.assertSequenceEqual(p3.get_sequences(), ())
