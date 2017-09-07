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


def main(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    server_address = args.server_address or os.environ.get(SERVER_ADDRESS_ENV_VAR, DEFAULT_SERVER)
    auth_token = args.auth_token or os.environ[AUTH_TOKEN_ENV_VAR]
    headers = dict(Authorization="Token " + auth_token)
    prefix = server_address + API_PREFIX + "user_tasks/"
    for task_id in args.task_ids:
        response = requests.get(prefix + str(task_id), headers=headers)
        assert response.ok, response
        task = response.json()
        passage = from_json(task)
        write_passage(passage, args.out_format, args.binary, args.out_dir, args.prefix, TO_FORMAT.get(args.out_format))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("task_ids", nargs="+", type=int, help="IDs of tasks to download and convert")
    argparser.add_argument("-f", "--out-format", choices=CONVERTERS, help="output file format (default: UCCA)")
    argparser.add_argument("-o", "--out-dir", default=".", help="output directory")
    argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
    argparser.add_argument("-b", "--binary", action="store_true", help="write in binary format (.pickle)")
    argparser.add_argument("-v", "--verbose", action="store_true", help="detailed output")
    argparser.add_argument("--server-address", default=DEFAULT_SERVER,
                           help="UCCA-App server, otherwise set by " + SERVER_ADDRESS_ENV_VAR)
    argparser.add_argument("--auth-token", help="authorization token, otherwise set by " + AUTH_TOKEN_ENV_VAR)
    main(argparser.parse_args())
    sys.exit(0)
