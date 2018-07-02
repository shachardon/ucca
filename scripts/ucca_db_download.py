from argparse import ArgumentParser

from scripts.ucca_db2 import get_by_xids
from ucca import convert
from ucca.ioutil import write_passage

desc = "Download passages to old UCCA annotation app"


def download_passage(xid, **kwargs):
    passages = get_by_xids(xids=[xid], **kwargs)
    return convert.from_site(passages[0])


def main(args):
    with open(args.filename, encoding="utf-8") as f:
        for passage_id, xid in map(str.split, f):
            passage = download_passage(xid, db_name=args.db_name, host_name=args.host_name)
            write_passage(passage, outdir=args.outdir, verbose=args.verbose)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("filename", help="specification filename with (passage ID, xid) per passage")
    argparser.add_argument("-d", "--db-name", default="work", help="database name")
    argparser.add_argument("-H", "--host-name", default="pgserver", help="host name")
    argparser.add_argument("-o", "--outdir", default=".", help="directory to write created XML IDs to")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
