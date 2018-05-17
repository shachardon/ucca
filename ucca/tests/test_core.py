"""Testing code for the ucca package, unit-testing only."""

from ucca import core, layer0, layer1
from .conftest import create_basic_passage, create_passage


def test_creation(self):
    p = create_basic_passage()

    self.assertEqual(p.ID, "1")
    self.assertEqual(p.root, p)
    self.assertDictEqual(p.attrib.copy(), {})
    self.assertEqual(p.layer("1").ID, "1")
    self.assertEqual(p.layer("2").ID, "2")
    self.assertRaises(KeyError, p.layer, "3")

    l1 = p.layer("1")
    l2 = p.layer("2")
    self.assertEqual(l1.root, p)
    self.assertEqual(l2.attrib["test"], True)
    self.assertNotEqual(l1.orderkey, l2.orderkey)
    self.assertSequenceEqual([x.ID for x in l1.all], ["1.1", "1.2", "1.3"])
    self.assertSequenceEqual([x.ID for x in l1.heads], ["1.2"])
    self.assertSequenceEqual([x.ID for x in l2.all], ["2.2", "2.1"])
    self.assertSequenceEqual([x.ID for x in l2.heads], ["2.2", "2.1"])

    node11, node12, node13 = l1.all
    node22, node21 = l2.all
    self.assertEqual(node11.ID, "1.1")
    self.assertEqual(node11.root, p)
    self.assertEqual(node11.layer.ID, "1")
    self.assertEqual(node11.tag, "1")
    self.assertEqual(len(node11), 0)
    self.assertSequenceEqual(node11.parents, [node12, node21, node22])
    self.assertSequenceEqual(node13.parents, [node12, node22])
    self.assertDictEqual(node13.attrib.copy(), {"node": True})
    self.assertEqual(len(node12), 2)
    self.assertSequenceEqual(node12.children, [node13, node11])
    self.assertDictEqual(node12[0].attrib.copy(), {"edge": True})
    self.assertSequenceEqual(node12.parents, [node22, node21])
    self.assertEqual(node21[0].ID, "2.1->1.1")
    self.assertEqual(node21[1].ID, "2.1->1.2")
    self.assertEqual(node22[0].ID, "2.2->1.1")
    self.assertEqual(node22[1].ID, "2.2->1.2")
    self.assertEqual(node22[2].ID, "2.2->1.3")


def test_modifying(self):
    p = create_basic_passage()
    l1, l2 = p.layer("1"), p.layer("2")
    node11, node12, node13 = l1.all
    node22, node21 = l2.all

    # Testing attribute changes
    p.attrib["passage"] = 1
    self.assertDictEqual(p.attrib.copy(), {"passage": 1})
    del l2.attrib["test"]
    self.assertDictEqual(l2.attrib.copy(), {})
    node13.attrib[1] = 1
    self.assertDictEqual(node13.attrib.copy(), {"node": True, 1: 1})
    self.assertEqual(len(node13.attrib), 2)
    self.assertEqual(node13.attrib.get("node"), True)
    self.assertEqual(node13.attrib.get("missing"), None)

    # Testing Node changes
    node14 = core.Node(ID="1.4", root=p, tag="4")
    node15 = core.Node(ID="1.5", root=p, tag="5")
    self.assertSequenceEqual(l1.all, [node11, node12, node13, node14,
                                      node15])
    self.assertSequenceEqual(l1.heads, [node12, node14, node15])
    node15.add("test", node11)
    self.assertSequenceEqual(node11.parents, [node12, node15, node21,
                                              node22])
    node21.remove(node12)
    node21.remove(node21[0])
    self.assertEqual(len(node21), 0)
    self.assertSequenceEqual(node12.parents, [node22])
    self.assertSequenceEqual(node11.parents, [node12, node15, node22])
    node14.add("test", node15)
    self.assertSequenceEqual(l1.heads, [node12, node14])
    node12.destroy()
    self.assertSequenceEqual(l1.heads, [node13, node14])
    self.assertSequenceEqual(node22.children, [node11, node13])

    node22.tag = "x"
    node22[0].tag = "testx"
    self.assertEqual(node22.tag, "x")
    self.assertEqual(node22[0].tag, "testx")


def test_equals(self):
    p1 = core.Passage("1")
    p2 = core.Passage("2")
    p1l0 = layer0.Layer0(p1)
    p2l0 = layer0.Layer0(p2)
    p1l1 = layer1.Layer1(p1)
    p2l1 = layer1.Layer1(p2)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))

    # Checks basic passage equality and Attrib/tag/len differences
    p1l0.add_terminal("0", False)
    p1l0.add_terminal("1", False)
    p1l0.add_terminal("2", False)
    p2l0.add_terminal("0", False)
    p2l0.add_terminal("1", False)
    p2l0.add_terminal("2", False)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    pnct2 = p2l0.add_terminal("3", True)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    temp = p1l0.add_terminal("3", False)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    temp.destroy()
    pnct1 = p1l0.add_terminal("3", True)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))

    # Check Edge and node equality
    ps1 = p1l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    ps2 = p2l1.add_fnode(None, layer1.EdgeTags.ParallelScene)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    p1l1.add_fnode(ps1, layer1.EdgeTags.Participant)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    self.assertTrue(ps1.equals(ps2, recursive=False))
    p2l1.add_fnode(ps2, layer1.EdgeTags.Process)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    p2l1.add_fnode(ps2, layer1.EdgeTags.Participant)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    p1l1.add_fnode(ps1, layer1.EdgeTags.Process)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    self.assertFalse(p1.equals(p2, ordered=True) or
                     p2.equals(p1, ordered=True))
    p1l1.add_fnode(ps1, layer1.EdgeTags.Adverbial, implicit=True)
    ps2d3 = p2l1.add_fnode(ps2, layer1.EdgeTags.Adverbial)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    ps2d3.attrib["implicit"] = True
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    ps2[2].attrib["remote"] = True
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    ps1[2].attrib["remote"] = True
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    p1l1.add_punct(None, pnct1)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))
    p2l1.add_punct(None, pnct2)
    self.assertTrue(p1.equals(p2) and p2.equals(p1))
    core.Layer("2", p1)
    self.assertFalse(p1.equals(p2) or p2.equals(p1))


def test_copying(self):
    # we don't need such a complex passage, but it will work anyway
    p1 = create_passage()

    p2 = p1.copy(())
    self.assertEqual(p1.ID, p2.ID)
    self.assertTrue(p1.attrib.equals(p2.attrib))
    self.assertEqual(p1.extra, p2.extra)
    self.assertEqual(p1.frozen, p2.frozen)

    l0id = layer0.LAYER_ID
    p2 = p1.copy([l0id])
    self.assertTrue(p1.layer(l0id).equals(p2.layer(l0id)))


def test_iteration(self):
    p = create_basic_passage()
    l1, l2 = p.layer("1"), p.layer("2")
    node11, node12, node13 = l1.all
    node22, node21 = l2.all

    self.assertSequenceEqual(list(node11.iter()), [node11])
    self.assertSequenceEqual(list(node11.iter(obj="edges")), ())
    self.assertSequenceEqual(list(node13.iter(key=lambda x: x.tag != "3")),
                             ())
    self.assertSequenceEqual(list(node12.iter()), [node12, node13, node11])
    self.assertSequenceEqual(list(x.ID for x in node12.iter(obj="edges")),
                             ["1.2->1.3", "1.2->1.1"])
    self.assertSequenceEqual(list(node21.iter(duplicates=True)),
                             [node21, node11, node12, node13, node11])
    self.assertSequenceEqual(list(node21.iter()),
                             [node21, node11, node12, node13])
    self.assertSequenceEqual(list(node22.iter(method="bfs",
                                              duplicates=True)),
                             [node22, node11, node12, node13, node13,
                              node11])
