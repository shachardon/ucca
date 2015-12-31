from ucca.layer1 import EdgeTags

ROOT_ID = "1.1"  # ID of root node in UCCA passages


class Constraints:
    # A unit may not have more than one outgoing edge with the same tag, if it is one of these:
    UniqueOutgoing = [
        EdgeTags.LinkRelation,
        EdgeTags.Process,
        EdgeTags.State,
    ]

    # A unit may not have more than one incoming edge with the same tag, if it is one of these:
    UniqueIncoming = [
        EdgeTags.Function,
        EdgeTags.Ground,
        EdgeTags.ParallelScene,
        EdgeTags.Linker,
        EdgeTags.LinkRelation,
        EdgeTags.Connector,
        EdgeTags.Punctuation,
        EdgeTags.Terminal,
    ]

    # A unit may not have more than one outgoing edge with any of these:
    MutuallyExclusiveOutgoing = [
        EdgeTags.Process,
        EdgeTags.State,
    ]

    # A unit may not have any children if it has any of these incoming edge tags:
    ChildlessIncoming = [
        EdgeTags.Function,
    ]

    # A unit with any outgoing edge with one of these tags is a scene:
    SceneSufficientOutgoing = [
        EdgeTags.Participant,
        EdgeTags.Process,
        EdgeTags.State,
    ]

    # A scene unit must have any outgoing edge with one of these tags:
    SceneNecessaryOutgoing = [
        EdgeTags.Process,
        EdgeTags.State,
    ]
