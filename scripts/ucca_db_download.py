import os
from argparse import ArgumentParser
from tqdm import tqdm
from xml.etree.ElementTree import tostring

from scripts.ucca_db2 import get_by_xids, get_most_recent_passage_by_uid
from ucca import convert
from ucca.ioutil import write_passage, external_write_mode

desc = "Download passages from old UCCA annotation app"


def get_by_method(method, id_field, passage_id=None, **kwargs):
    if method == "xid":
        return get_by_xids(xids=[id_field], **kwargs)[0]
    elif method == "uid":
        return get_most_recent_passage_by_uid(id_field, passage_id, **kwargs)
    raise ValueError("Unknown method: '%s'" % method)


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    with open(args.filename, encoding="utf-8") as f:
        t = tqdm(list(map(str.split, f)), desc="Downloading", unit=" passages")
        for passage_id, id_field in t:
            t.set_postfix({"passage_id": passage_id, args.method: id_field})
            if args.verbose:
                with external_write_mode():
                    print("Getting passage " + passage_id + " with " + args.method + "=" + id_field)
            xml_root = get_by_method(id_field=id_field, passage_id=passage_id, **vars(args))
            if args.write_site:
                site_filename = passage_id + "_site_download.xml"
                with open(site_filename, "w", encoding="utf-8") as fsite:
                    print(tostring(xml_root).decode(), file=fsite)
                if args.verbose:
                    with external_write_mode():
                        print("Wrote '%s'" % site_filename)
            if args.write:
                write_passage(convert.from_site(xml_root), outdir=args.outdir, verbose=args.verbose)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("filename", help="specification filename with (passage ID, xid OR uid) per passage")
    argparser.add_argument("-m", "--method", default="uid", choices=("xid", "uid"), help="by xid or latest by paid,uid")
    argparser.add_argument("-d", "--db-name", default="work", help="database name")
    argparser.add_argument("-H", "--host-name", default="pgserver", help="host name")
    argparser.add_argument("-o", "--outdir", default=".", help="directory to write created XML IDs to")
    argparser.add_argument("-s", "--write-site", action="store_true", help="write site format, too, for debugging")
    argparser.add_argument("-n", "--no-write", dest="write", action="store_false", help="do not really write any files")
    argparser.add_argument("-x", "--write-xids", help="file to write xids to (for `uid' method)")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
