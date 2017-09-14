#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys

import requests

from ucca.convert import from_json, CONVERTERS, TO_FORMAT
from ucca.ioutil import write_passage

desc = """Download task from UCCA-App and convert to a passage in standard format"""

DEFAULT_SERVER = "http://ucca-demo.cs.huji.ac.il"
API_PREFIX = "/api/v1/"
SERVER_ADDRESS_ENV_VAR = "UCCA_APP_SERVER_ADDRESS"
AUTH_TOKEN_ENV_VAR = "UCCA_APP_AUTH_TOKEN"
EMAIL_ENV_VAR = "UCCA_APP_EMAIL"
PASSWORD_ENV_VAR = "UCCA_APP_PASSWORD"


class ServerAccessor(object):
    def __init__(self, server_address, email, password, auth_token, verbose, **kwargs):
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        server_address = server_address or os.environ.get(SERVER_ADDRESS_ENV_VAR, DEFAULT_SERVER)
        self.headers = {}
        self.prefix = server_address + API_PREFIX
        token = auth_token or os.environ.get(AUTH_TOKEN_ENV_VAR)
        if not token:
            token = self.request("post", "login", json=dict(
                email=email or os.environ[EMAIL_ENV_VAR],
                password=password or os.environ[PASSWORD_ENV_VAR])).json()["token"]
        self.headers["Authorization"] = "Token " + token

    def request(self, method, url_suffix, **kwargs):
        response = requests.request(method, self.prefix + str(url_suffix), headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("--server-address", help="UCCA-App server, otherwise set by " + SERVER_ADDRESS_ENV_VAR)
        argparser.add_argument("--email", help="UCCA-App email, otherwise set by " + EMAIL_ENV_VAR)
        argparser.add_argument("--password", help="UCCA-App password, otherwise set by " + PASSWORD_ENV_VAR)
        argparser.add_argument("--auth-token", help="authorization token (required only if email or password missing), "
                                                    "otherwise set by " + AUTH_TOKEN_ENV_VAR)
        argparser.add_argument("-v", "--verbose", action="store_true", help="detailed output")


class TaskDownloader(ServerAccessor):
    def download_tasks(self, task_ids, **kwargs):
        for task_id in task_ids:
            yield self.download_task(task_id, **kwargs)

    def download_task(self, task_id, write=True, out_format=None, binary=None, out_dir=None, prefix=None, **kwargs):
        del kwargs
        logging.debug("Getting task " + str(task_id))
        task = self.request("get", "user_tasks/" + str(task_id)).json()
        logging.debug("Got task: " + json.dumps(task))
        passage = from_json(task)
        if write:
            write_passage(passage, out_format, binary, out_dir, prefix, TO_FORMAT.get(out_format))
        return passage

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("task_ids", nargs="+", type=int, help="IDs of tasks to download and convert")
        TaskDownloader.add_write_arguments(argparser)
        ServerAccessor.add_arguments(argparser)

    @staticmethod
    def add_write_arguments(argparser):
        argparser.add_argument("-f", "--out-format", choices=CONVERTERS, help="output file format (default: UCCA)")
        argparser.add_argument("-o", "--out-dir", default=".", help="output directory")
        argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
        argparser.add_argument("-b", "--binary", action="store_true", help="write in binary format (.pickle)")


def main(**kwargs):
    list(TaskDownloader(**kwargs).download_tasks(**kwargs))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
