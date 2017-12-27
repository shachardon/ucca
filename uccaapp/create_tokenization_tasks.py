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

desc = """Upload a list of tokenization tasks to a project"""

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
            user_obj = self.get_user(user_id)
            passage_obj = self.get_passage(fields[1])
            task_in = dict(type="TOKENIZATION", status="NOT_STARTED", project=self.project,
                           user=self.user, passage=passage_obj,
                           manager_comment="passage #"+str(passage_obj['id']),
                           user_comment='', parent=None,
                           is_demo=False, is_active=True)
            tok_task_out = self.create_tokenization_task(**task_in)
            sys.stderr.write('Task #'+str(tok_task_out['id'])+' uploaded.\n')
            num += 1
        sys.stderr.write('Uploaded '+str(num)+ ' tasks successfully.\n')

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename",
                               help="a file where each line is a <User ID> <Passage ID>")
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
