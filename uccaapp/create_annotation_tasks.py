#!/usr/bin/env python3
import argparse
import os, pdb
import sys
from glob import glob

from requests.exceptions import HTTPError

from ucca.convert import to_json, to_text
from ucca.ioutil import read_files_and_dirs
from uccaapp.api import ServerAccessor

try:
    from simplejson.scanner import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError

desc = """Convert a passage file to JSON format and upload to UCCA-App as a completed task"""

# https://github.com/omriabnd/UCCA-App/blob/master/UCCAApp_REST_API_Reference.pdf
# ucca-demo.cs.huji.ac.il or ucca.staging.cs.huji.ac.il
# upload the parse as a (completed) task:
# 0. decide which project and user you want to assign it to
# 1. POST passage (easy format)
# 2. POST task x (of type tokenization)
# 3. PUT task x (submit)
# 4. POST task y (of type annotation with parent x; this is the more complicated format)
# 5. PUT task y (submit)

USER_ID_ENV_VAR = "UCCA_APP_USER_ID"


class TaskUploader(ServerAccessor):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user = dict(id=user_id or int(os.environ[USER_ID_ENV_VAR]))

    def upload_task(self, inp_filename):
        f = open(inp_filename)
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
                           passage=tok_task_out['passage'], manager_comment="Reviews corpus",
                           user_comment="Test", parent=tok_task_out,
                           is_demo=False, is_active=True)
            ann_user_task_in = self.create_annotation_task(**task_in)
            num += 1
        sys.stderr.write('Uploaded '+str(num)+ ' tasks successfully.\n')

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename",
                               help="a file where each line is a <User ID> <TOKENIZATION TASK ID>")
        argparser.add_argument("--user-id",
                               type=int, help="user id, otherwise set by " + USER_ID_ENV_VAR)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    TaskUploader(**kwargs).upload_task(kwargs['filename'])


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
