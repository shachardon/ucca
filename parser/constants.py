from ucca import layer1

ROOT_ID = "1.1"  # ID of root node in UCCA passages

# A unit may not have more than one outgoing edge with the same tag, if it is one of these:
UNIQUE_OUTGOING = [
    layer1.EdgeTags.LinkRelation,
    layer1.EdgeTags.Process,
    layer1.EdgeTags.State,
]

# A unit may not have more than one incoming edge with the same tag, if it is one of these:
UNIQUE_INCOMING = [
    layer1.EdgeTags.Function,
    layer1.EdgeTags.Ground,
    layer1.EdgeTags.ParallelScene,
    layer1.EdgeTags.Linker,
    layer1.EdgeTags.LinkRelation,
    layer1.EdgeTags.Connector,
    layer1.EdgeTags.Punctuation,
    layer1.EdgeTags.Terminal,
]

# A unit may not have any children if it has any of these incoming edge tags:
CHILDLESS_INCOMING = [
    layer1.EdgeTags.Function,
]