#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from glob import glob
try:
    from simplejson.scanner import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError

from requests.exceptions import HTTPError

from convert import to_json, to_text
from download_task import ServerAccessor
from ucca.ioutil import read_files_and_dirs

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
PROJECT_ID_ENV_VAR = "UCCA_APP_PROJECT_ID"
SOURCE_ID_ENV_VAR = "UCCA_APP_SOURCE_ID"


class TaskUploader(ServerAccessor):
    def __init__(self, user_id, project_id, source_id, **kwargs):
        super().__init__(**kwargs)
        self.user = dict(id=user_id or int(os.environ[USER_ID_ENV_VAR]))
        self.project = dict(id=project_id or int(os.environ[PROJECT_ID_ENV_VAR]))
        self.source_id = source_id or int(os.environ[SOURCE_ID_ENV_VAR])
        
    def upload_tasks(self, filenames, **kwargs):
        del kwargs
        try:
            for pattern in filenames:
                filenames = glob(pattern)
                if not filenames:
                    raise IOError("Not found: " + pattern)
                for p in read_files_and_dirs(filenames):
                    source = self.request("get", "sources/%d/" % self.source_id).json()
                    logging.debug("Got source: " + str(source))
                    text = to_text(p, sentences=False)[0]
                    passage = self.request("post", "passages/",
                                           json=dict(text=text, type="PUBLIC", source=source)).json()
                    logging.debug("Created passage: " + str(passage))
                    tok_task = self.request("post", "tasks/",
                                            json=dict(type="TOKENIZATION", status="SUBMITTED", project=self.project,
                                                      passage=passage, user=self.user, parent=False, is_demo=False,
                                                      manager_comment="Passage " + p.ID, is_active=True)).json()
                    logging.debug("Created tokenization task: " + str(tok_task))
                    self.request("put", "user_tasks/%d/submit" % tok_task["id"])
                    task = self.request("post", "tasks/",
                                        json=dict(parent=tok_task, children=[], type="ANNOTATION", status="SUBMITTED",
                                                  project=self.project, user=self.user, passage=passage, is_demo=False,
                                                  manager_comment="Passage " + p.ID, is_active=True)).json()
                    logging.debug("Created annotation task: " + str(task))
                    user_task = to_json(p, return_dict=True)
                    user_task.update(dict(parent=task, children=[], type="ANNOTATION", status="SUBMITTED",
                                          project=self.project, user=self.user, passage=passage, is_demo=False,
                                          manager_comment="Passage " + p.ID, is_active=True))
                    self.request("put", "user_tasks/%d/submit" % task["id"], json=user_task)
                    print("Submitted task %d" % task["id"])
        except HTTPError as e:
            try:
                raise ValueError(e.response.json()) from e
            except JSONDecodeError:
                raise ValueError(e.response.text) from e

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filenames", nargs="+", help="passage file names to convert and upload")
        argparser.add_argument("--user-id", type=int, help="user id, otherwise set by " + USER_ID_ENV_VAR)
        argparser.add_argument("--project-id", type=int, help="project id, otherwise set by " + PROJECT_ID_ENV_VAR)
        argparser.add_argument("--source-id", type=int, help="source id, otherwise set by " + SOURCE_ID_ENV_VAR)
        ServerAccessor.add_arguments(argparser)


def main(kwargs):
    TaskUploader(**kwargs).upload_tasks(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskUploader.add_arguments(argument_parser)
    main(vars(argument_parser.parse_args()))
    sys.exit(0)
