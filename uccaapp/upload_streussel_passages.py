#!/usr/bin/env python3
import argparse, pdb
import os
import sys
from glob import glob

from requests.exceptions import HTTPError

from ucca.convert import to_json, from_text
from ucca.ioutil import read_files_and_dirs
from uccaapp.api import ServerAccessor

try:
    from simplejson.scanner import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError

desc = """Upload a passage from a streussel format file"""

USER_ID_ENV_VAR = "UCCA_APP_USER_ID"

class StreusselPassageUploader(ServerAccessor):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user = dict(id=user_id or int(os.environ[USER_ID_ENV_VAR]))
        
    def upload_streussel_passage_file(self, filenames):
        filenames_handle = open(filenames)
        for filename in filenames_handle:
            passage_text = ''
            external_id = 'None given'
            filename = filename.strip()
            f = open(filename)
            for line in f:
                line = line.strip()
                if line == '':
                    continue
                elif line.startswith('#'):
                    fields = line.split()
                    if len(fields) != 4 or fields[1] != 'sent_id':
                        sys.stderr.write("FORMAT ERROR in "+filename+'\n')
                    else:
                        external_id = fields[3].split('-')[1]
                else:
                    passage_text = passage_text + ' ' + line
            passage_out = self.create_passage(text=passage_text, external_id=external_id, type="PUBLIC", source=self.source)
            task_in = dict(type="TOKENIZATION", status="SUBMITTED", project=self.project,
                           user=self.user, passage=passage_out, manager_comment='External ID: '+external_id,
                           user_comment='', parent=None, is_demo=False, is_active=True)
            tok_task_out = self.create_tokenization_task(**task_in)
            tok_user_task_in = dict(tok_task_out)

            passage = list(from_text(passage_text.split(),tokenized=True))[0]
            tok_user_task_in.update(to_json(passage, return_dict=True, tok_task=True))

            tok_user_task_out = self.submit_tokenization_task(**tok_user_task_in)
            sys.stderr.write("Uploaded Passage "+filename+' successful.\n')
            
           

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filenames", help="passage file names to convert and upload")
        argparser.add_argument("--user-id", type=int, help="user id, otherwise set by " + USER_ID_ENV_VAR)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    StreusselPassageUploader(**kwargs).upload_streussel_passage_file(kwargs['filenames'])


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    StreusselPassageUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)

