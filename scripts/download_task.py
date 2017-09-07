#!/usr/bin/env python3
import argparse
import logging
import os
import sys

import requests

from convert import from_json, CONVERTERS, TO_FORMAT
from ioutil import write_passage

desc = """Download task from UCCA-App and convert to a passage in standard format"""

DEFAULT_SERVER = "http://ucca-demo.cs.huji.ac.il"
API_PREFIX = "/api/v1/"
SERVER_ADDRESS_ENV_VAR = "UCCA_APP_SERVER_ADDRESS"
AUTH_TOKEN_ENV_VAR = "UCCA_APP_AUTH_TOKEN"


class ServerAccessor(object):
    def __init__(self, server_address, auth_token, verbose, **kwargs):
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        server_address = server_address or os.environ.get(SERVER_ADDRESS_ENV_VAR, DEFAULT_SERVER)
        auth_token = auth_token or os.environ[AUTH_TOKEN_ENV_VAR]
        self.headers = dict(Authorization="Token " + auth_token)
        self.prefix = server_address + API_PREFIX + "user_tasks/"

    def request(self, method, url_suffix, **kwargs):
        response = requests.request(method, self.prefix + str(url_suffix), headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("--server-address", default=DEFAULT_SERVER,
                               help="UCCA-App server, otherwise set by " + SERVER_ADDRESS_ENV_VAR)
        argparser.add_argument("--auth-token", help="authorization token, otherwise set by " + AUTH_TOKEN_ENV_VAR)
        argparser.add_argument("-v", "--verbose", action="store_true", help="detailed output")


class TaskDownloader(ServerAccessor):
    def download_tasks(self, task_ids, out_format, binary, out_dir, prefix, **kwargs):
        del kwargs
        for task_id in task_ids:
            task = self.request("get", str(task_id)).json()
            passage = from_json(task)
            write_passage(passage, out_format, binary, out_dir, prefix, TO_FORMAT.get(out_format))

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("task_ids", nargs="+", type=int, help="IDs of tasks to download and convert")
        argparser.add_argument("-f", "--out-format", choices=CONVERTERS, help="output file format (default: UCCA)")
        argparser.add_argument("-o", "--out-dir", default=".", help="output directory")
        argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
        argparser.add_argument("-b", "--binary", action="store_true", help="write in binary format (.pickle)")
        ServerAccessor.add_arguments(argparser)


def main(kwargs):
    TaskDownloader(**kwargs).download_tasks(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    main(vars(argument_parser.parse_args()))
    sys.exit(0)
