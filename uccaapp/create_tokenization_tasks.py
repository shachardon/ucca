#!/usr/bin/env python3
import argparse
import sys

from uccaapp.api import ServerAccessor

desc = """Upload a list of tokenization tasks to a project"""


class TokenizationTaskCreator(ServerAccessor):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.set_user(user_id)

    def create_task(self, filename, **kwargs):
        del kwargs
        with open(filename, encoding="utf-8") as f:
            num = 0
            for line in f:
                fields = line.strip().split()
                if len(fields) != 2:
                    sys.stderr.write("Error in line: "+line.strip())
                    continue
                user_id = fields[0]
                user_obj = self.get_user(user_id)
                passage_obj = self.get_passage(fields[1])
                task_in = dict(type="TOKENIZATION", status="NOT_STARTED", project=self.project,
                               user=user_obj, passage=passage_obj,
                               manager_comment="passage #%s" % passage_obj["id"],
                               user_comment="", parent=None,
                               is_demo=False, is_active=True)
                tok_task_out = self.create_tokenization_task(**task_in)
                print("Task #%s uploaded." % tok_task_out["id"], file=sys.stderr)
                num += 1
            print("Uploaded %d tasks successfully." % num, file=sys.stderr)

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="a file where each line is a <User ID> <Passage ID>")
        ServerAccessor.add_user_id_argument(argparser)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    TokenizationTaskCreator(**kwargs).create_task(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TokenizationTaskCreator.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
