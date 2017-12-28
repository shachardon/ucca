#!/usr/bin/env python3
import argparse
import sys

from ucca.convert import from_text, to_json
from uccaapp.api import ServerAccessor

desc = """Upload a passage from a streussel format file"""


class StreusselPassageUploader(ServerAccessor):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.set_user(user_id)
        
    def upload_streussel_passage_file(self, filenames, **kwargs):
        del kwargs
        with open(filenames) as f_all:
            for filename in f_all:
                passage_text = ""
                external_id = "None given"
                filename = filename.strip()
                with open(filename, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        elif line.startswith("#"):
                            fields = line.split()
                            if len(fields) != 4 or fields[1] != "sent_id":
                                print("FORMAT ERROR in "+filename, file=sys.stderr)
                            else:
                                external_id = fields[3].split("-")[1]
                        else:
                            passage_text = passage_text + " " + line
                passage_out = self.create_passage(text=passage_text.strip(), external_id=external_id, type="PUBLIC",
                                                  source=self.source)
                task_in = dict(type="TOKENIZATION", status="SUBMITTED", project=self.project,
                               user=self.user, passage=passage_out, manager_comment="External ID: "+external_id,
                               user_comment="", parent=None, is_demo=False, is_active=True)
                tok_task_out = self.create_tokenization_task(**task_in)
                tok_user_task_in = dict(tok_task_out)

                passage = list(from_text(passage_text.split(),tokenized=True))[0]
                tok_user_task_in.update(to_json(passage, return_dict=True, tok_task=True))

                self.submit_tokenization_task(**tok_user_task_in)
                print("Uploaded Passage "+filename+" successful.", file=sys.stderr)
            

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filenames", help="passage file names to convert and upload")
        ServerAccessor.add_user_id_argument(argparser)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    StreusselPassageUploader(**kwargs).upload_streussel_passage_file(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    StreusselPassageUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)

