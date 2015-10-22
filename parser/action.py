import re


class Action:
    def __init__(self, action_type, tag=None, node_id=None):
        self.type = action_type
        self.tag = tag
        self.node_id = node_id  # During training, created node ID from gold passage (if relevant)

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
        return self.type == other.type and self.tag == other.tag


SHIFT = Action("SHIFT")
REDUCE = Action("REDUCE")
FINISH = Action("FINISH")