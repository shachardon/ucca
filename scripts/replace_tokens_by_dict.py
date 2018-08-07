from html import escape
import argparse
import os

desc = """Replaces the tokens according to a dictionary."""


def read_dictionary_from_file(filename):
    f = open(filename,encoding="utf-8")
    D = {}
    for line in f:
        fields = line.strip().split()
        D[fields[0].strip().encode('ascii','xmlcharrefreplace').decode()] = fields[1].strip().encode('ascii','xmlcharrefreplace').decode()
    print(D)
    return D

def main(args):
    os.makedirs(args.out_dir, exist_ok=True)
    replacement_dict = read_dictionary_from_file(args.dict)
    for filename in args.filenames:
        basename = os.path.splitext(os.path.basename(filename))[0]
        outfile = open(args.out_dir + os.path.sep + basename + ".txt","w",encoding="utf-8")
        xml_string = open(filename).read()
        for k,v in replacement_dict.items():
            xml_string = xml_string.replace("text=\""+k+"\"","text=\""+v+"\"")
        print(xml_string, file=outfile)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="files or directories to replace tokens in")
    argparser.add_argument("-o", "--out-dir", default=".", help="output directory for changed XMLs")
    argparser.add_argument("-d", "--dict",
             help="filename to read the dictionary from. the file should have one line per entry, in the" +
                  " format of <original text> <replaced text>")
    main(argparser.parse_args())




