from argparse import ArgumentParser
from xml.etree.ElementTree import tostring

from scripts.ucca_db2 import CONNECTION, write_to_db
from ucca import convert
from ucca.ioutil import get_passages_with_progress_bar

desc = "Upload passages to old UCCA annotation app"


def upload_passage(xml_root, **kwargs):
    decoded = tostring(xml_root).decode()
    with open("temp.xml", "w", encoding="utf-8") as f:
        print(decoded, file=f)
    return write_to_db(xml=decoded, **kwargs)


def main(args):
    with open(args.out, "w", encoding="utf-8") as f:
        for passage in get_passages_with_progress_bar(args.passages):
            out = upload_passage(convert.to_site(passage), db_name=args.db_name, host_name=args.host_name,
                                 new_pid=passage.ID, new_prid=args.project_id, username=args.username)
            print(passage.ID, out, file=f)
    if CONNECTION is not None:
        CONNECTION.commit()
    print("Wrote '%s'" % args.out)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    argparser.add_argument("-d", "--db-name", default="work", help="database name")
    argparser.add_argument("-H", "--host-name", default="pgserver", help="host name")
    argparser.add_argument("-p", "--project-id", default="63", help="project ID")
    argparser.add_argument("-u", "--username", default="danielh", help="username")
    argparser.add_argument("-o", "--out", default="xids.txt", help="file to write created XML IDs to")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
