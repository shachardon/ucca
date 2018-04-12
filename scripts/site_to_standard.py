#! /usr/bin/python3

import argparse
import os
import pickle
import sqlite3
from xml.etree.ElementTree import ElementTree, tostring, fromstring

import ucca.convert
from ucca.textutil import indent_xml

desc = """Parses an XML in UCCA site format.

The input can be given as either an XML file or a DB file with passage ID
and user name, and the output is either the standard format XML or
a pickled object.
Possible input methods are using a DB file with pid and user, which gets the
annotation of the specified user for the specified passage from teh DB file,
or using filenames of a site-formatted XML file.

"""


def site2passage(filename):
    """Opens a file and returns its parsed Passage object"""
    with open(filename, encoding="utf-8") as f:
        etree = ElementTree().parse(f)
    return ucca.convert.from_site(etree)


def db2passage(handle, pid, user):
    """Gets the annotation of user to pid from the DB handle - returns a passage"""
    handle.execute("SELECT id FROM users WHERE username=?", (user,))
    uid = handle.fetchone()[0]
    handle.execute("SELECT xml FROM xmls WHERE paid=? AND uid=? " +
                   "ORDER BY ts DESC", (pid, uid))
    raw_xml = handle.fetchone()[0]
    return ucca.convert.from_site(fromstring(raw_xml))


def outfile(source, target, suffix):
    return os.path.join(target, os.path.splitext(source)[0] + suffix) if os.path.isdir(target) else target


def main(args):
    if args.filenames:
        passages = ((filename, site2passage(filename)) for filename in args.filenames)
    else:
        conn = sqlite3.connect(args.db)
        c = conn.cursor()
        passages = ((pid, db2passage(c, pid, args.user)) for pid in args.pids)

    for filename, passage in passages:
        if args.binary:
            with open(outfile(filename, args.binary, ".pickle"), "wb") as binf:
                pickle.dump(passage, binf)
        else:
            root = ucca.convert.to_standard(passage)
            output = indent_xml(tostring(root).decode())
            if args.outfile:
                with open(outfile(filename, args.outfile, ".xml"), "w", encoding="utf-8") as outf:
                    outf.write(output)
            else:
                print(output)


def check_illegal_combinations(args):
    if args.db and args.filenames:
        argparser.error("Only one source, XML or DB file, can be used")
    if (not args.db) and (not args.filenames):
        argparser.error("Must specify one source, XML or DB file")
    if args.db and not (args.pids and args.user):
        argparser.error("Must specify a username and a passage ID when " +
                        "using DB file option")
    if (args.pids or args.user) and not args.db:
        argparser.error("Cannot use user and passage ID options without DB file")
    return args


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="*", help="XML file name to convert")
    argparser.add_argument("-o", "--outfile", help="output file for standard XML")
    argparser.add_argument("-b", "--binary", help="output file for binary pickle")
    argparser.add_argument("-d", "--db", help="DB file to get input from")
    argparser.add_argument("-p", "--pids", nargs="*", type=int, help="PassageIDs to query DB")
    argparser.add_argument("-u", "--user", help="Username to DB query")
    main(check_illegal_combinations(argparser.parse_args()))
