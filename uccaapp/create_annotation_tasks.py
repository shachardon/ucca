#!/usr/bin/env python3
import argparse
import sys

from uccaapp.api import ServerAccessor

desc = """Convert a passage file to JSON format and upload to UCCA-App as a completed task"""


class AnnotationTaskCreator(ServerAccessor):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.set_user(user_id)

    def create_task(self, filename, **kwargs):
        del kwargs
        with open(filename) as f:
            num = 0
            for line in f:
                fields = line.strip().split()
                if len(fields) != 2:
                    sys.stderr.write("Error in line: "+line.strip())
                    continue
                user_id = fields[0]
                user_model = self.get_user(user_id)
                tok_task_out = self.get_task(fields[1])
                task_in = dict(type="ANNOTATION", status="SUBMITTED",
                               project=self.project, user=user_model,
                               passage=tok_task_out["passage"], manager_comment="Reviews corpus",
                               user_comment="Test", parent=tok_task_out,
                               is_demo=False, is_active=True)
                self.create_annotation_task(**task_in)
                num += 1
            print("Uploaded %d tasks successfully." % num, file=sys.stderr)

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="a file where each line is a <User ID> <TOKENIZATION TASK ID>")
        ServerAccessor.add_user_id_argument(argparser)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    AnnotationTaskCreator(**kwargs).create_task(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    AnnotationTaskCreator.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
