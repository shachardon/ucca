import re
from pip.utils import cached_property


class Action:
    def __init__(self, action_type, tag=None, orig_node=None):
        self.type = action_type  # String
        self.tag = tag  # Usually the tag of the created edge; but if COMPOUND_SWAP, the distance
        self.orig_node = orig_node  # Node created by this action, if any (during training)

    @staticmethod
    def from_string(s):
        m = re.match("(.*)-(.*)", s)
        if m:  # String contains tag
            action_type, tag = m.groups()
            return Action(action_type, tag)
        return Action(s)

    def __repr__(self):
        return Action.__name__ + "(" + self.type + (", " + self.tag if self.tag else "") + ")"

    def __str__(self):
        return self.type + ("-" + str(self.tag) if self.tag else "")

    def __eq__(self, other):
        return self.type == other.type

    def __call__(self, *args, **kwargs):
        return Action(self.type, *args, **kwargs)

    @cached_property
    def parent(self):
        if self in (LEFT_EDGE, LEFT_REMOTE):
            return -1
        elif self in (RIGHT_EDGE, RIGHT_REMOTE):
            return -2
        elif self == NODE:
            return -1
        return None

    @cached_property
    def child(self):
        if self in (LEFT_EDGE, LEFT_REMOTE):
            return -2
        elif self in (RIGHT_EDGE, RIGHT_REMOTE):
            return -1
        elif self == IMPLICIT:
            return -1
        return None

    @cached_property
    def remote(self):
        return self in (LEFT_REMOTE, RIGHT_REMOTE)


SHIFT = Action("SHIFT")
NODE = Action("NODE")
IMPLICIT = Action("IMPLICIT")
REDUCE = Action("REDUCE")
LEFT_EDGE = Action("LEFT-EDGE")
RIGHT_EDGE = Action("RIGHT-EDGE")
LEFT_REMOTE = Action("LEFT-REMOTE")
RIGHT_REMOTE = Action("RIGHT-REMOTE")
SWAP = Action("SWAP")
FINISH = Action("FINISH")
