from ucca.tree import *

os.chdir("..")
try:
    trees = load_trees()
except FileNotFoundError:
    trees = build_trees()

fname = "trees/data.txt"
with open(fname, "w") as f:
    f.writelines([str(tree) + "\n" for tree in trees])
print("Wrote '%s'" % fname)