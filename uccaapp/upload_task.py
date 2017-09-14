#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from glob import glob

from requests.exceptions import HTTPError

from ucca.convert import to_json, to_text
from ucca.ioutil import read_files_and_dirs
from uccaapp.download_task import ServerAccessor

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
PROJECT_ID_ENV_VAR = "UCCA_APP_PROJECT_ID"
SOURCE_ID_ENV_VAR = "UCCA_APP_SOURCE_ID"


class TaskUploader(ServerAccessor):
    def __init__(self, user_id, project_id, source_id, **kwargs):
        super().__init__(**kwargs)
        self.user_in = dict(id=user_id or int(os.environ[USER_ID_ENV_VAR]))
        self.project_id = project_id or int(os.environ[PROJECT_ID_ENV_VAR])
        self.source_id = source_id or int(os.environ[SOURCE_ID_ENV_VAR])
        
    def upload_tasks(self, filenames, **kwargs):
        del kwargs
        try:
            for pattern in filenames:
                filenames = glob(pattern)
                if not filenames:
                    raise IOError("Not found: " + pattern)
                for passage in read_files_and_dirs(filenames):
                    yield self.upload_task(passage)
        except HTTPError as e:
            try:
                raise ValueError(e.response.json()) from e
            except JSONDecodeError:
                raise ValueError(e.response.text) from e

    def upload_task(self, passage):
        # Get source
        logging.debug("Getting source %d" % self.source_id)
        source_out = self.request("get", "sources/%d/" % self.source_id).json()
        logging.debug("Got source: " + json.dumps(source_out))
        # Get project
        logging.debug("Getting project %d" % self.project_id)
        project_out = self.request("get", "projects/%d/" % self.project_id).json()
        logging.debug("Got project: " + json.dumps(project_out))
        # Get layer
        layer_id = project_out["layer"]["id"]
        logging.debug("Getting layer %d" % layer_id)
        layer_out = self.request("get", "layers/%d/" % layer_id).json()
        logging.debug("Got layer: " + json.dumps(layer_out))
        # Create passage
        passage_in = dict(text=to_text(passage, sentences=False)[0], type="PUBLIC", source=source_out)
        logging.debug("Creating passage: " + json.dumps(passage_in))
        passage_out = self.request("post", "passages/", json=passage_in).json()
        logging.debug("Created passage: " + json.dumps(passage_out))
        # Create tokenization task
        tok_task_in = dict(type="TOKENIZATION", status="SUBMITTED", project=project_out, user=self.user_in,
                           passage=passage_out, manager_comment=passage.ID, parent=None, is_demo=False, is_active=True)
        logging.debug("Creating tokenization task: " + json.dumps(tok_task_in))
        tok_task_out = self.request("post", "tasks/", json=tok_task_in).json()
        logging.debug("Created tokenization task: " + json.dumps(tok_task_out))
        # Submit tokenization task
        tok_user_task_in = dict(tok_task_out)
        tok_user_task_in.update(to_json(passage, return_dict=True, tok_task=True))
        logging.debug("Submitting tokenization task: " + json.dumps(tok_user_task_in))
        tok_user_task_out = self.request("put", "user_tasks/%d/submit" % tok_task_out["id"],
                                         json=tok_user_task_in).json()
        logging.debug("Submitted tokenization task: " + json.dumps(tok_user_task_out))
        # Create annotation task
        ann_task_in = dict(tok_task_in)
        ann_task_in.update(dict(parent=tok_task_out, type="ANNOTATION"))
        logging.debug("Creating annotation task: " + json.dumps(ann_task_in))
        ann_task_out = self.request("post", "tasks/", json=ann_task_in).json()
        logging.debug("Created annotation task: " + json.dumps(ann_task_out))
        # Submit annotation task
        ann_user_task_in = dict(ann_task_out)
        ann_user_task_in.update(
            to_json(passage, return_dict=True, tok_task=tok_user_task_out, all_categories=layer_out["categories"]))
        logging.debug("Submitting annotation task: " + json.dumps(ann_user_task_in))
        ann_user_task_out = self.request("put", "user_tasks/%d/submit" % ann_task_out["id"],
                                         json=ann_user_task_in).json()
        logging.debug("Submitted annotation task: " + json.dumps(ann_user_task_out))
        print("Submitted task %d" % ann_user_task_out["id"])
        return ann_user_task_out

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filenames", nargs="+", help="passage file names to convert and upload")
        argparser.add_argument("--user-id", type=int, help="user id, otherwise set by " + USER_ID_ENV_VAR)
        argparser.add_argument("--project-id", type=int, help="project id, otherwise set by " + PROJECT_ID_ENV_VAR)
        argparser.add_argument("--source-id", type=int, help="source id, otherwise set by " + SOURCE_ID_ENV_VAR)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    list(TaskUploader(**kwargs).upload_tasks(**kwargs))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)