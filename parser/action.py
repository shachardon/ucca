import re

from config import Config
from ucca import layer1


class Action(object):
    type_to_id = {}
    all_actions = None
    all_action_ids = None

    def __init__(self, action_type, tag=None, orig_node=None):
        self.type = action_type  # String
        self.tag = tag  # Usually the tag of the created edge; but if COMPOUND_SWAP, the distance
        self.orig_node = orig_node  # Node created by this action, if any (during training)
        self.edge = None  # Will be set by State when the edge created by this action is known

        self.type_id = Action.type_to_id.get(self.type)  # Allocate ID for fast comparison
        if self.type_id is None:
            self.type_id = len(Action.type_to_id)
            Action.type_to_id[self.type] = self.type_id
        self._id = None

    def is_type(self, *others):
        return self.type_id in (o.type_id for o in others)

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
        return self.id == other.id

    def __call__(self, *args, **kwargs):
        return Action(self.type, *args, **kwargs)

    @property
    def remote(self):
        return self.is_type(LEFT_REMOTE, RIGHT_REMOTE)

    @property
    def id(self):
        if self._id is None:
            Action.get_all_actions()
            self._id = Action.all_action_ids[(self.type_id, self.tag)]
        return self._id

    @classmethod
    def get_all_actions(cls):
        if cls.all_actions is None:
            cls.all_actions = [action(tag) for action in
                               (NODE, IMPLICIT, LEFT_EDGE, RIGHT_EDGE, LEFT_REMOTE, RIGHT_REMOTE)
                               for name, tag in layer1.EdgeTags.__dict__.items()
                               if isinstance(tag, str) and not name.startswith('__')] + \
                              [REDUCE, SHIFT, FINISH]
            if Config().compound_swap:
                cls.all_actions.extend(SWAP(i) for i in range(1, Config().max_swap + 1))
            else:
                cls.all_actions.append(SWAP)
            cls.all_action_ids = {(action.type_id, action.tag): i
                                  for i, action in enumerate(cls.all_actions)}
        return cls.all_actions

    @classmethod
    def by_id(cls, i):
        return cls.get_all_actions()[i]


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
