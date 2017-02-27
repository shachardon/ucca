"""Utility functions for UCCA scripts."""
import os
import pickle
import sys
import time
from xml.etree.ElementTree import ElementTree, tostring
from xml.etree.ElementTree import ParseError

from ucca.convert import from_standard, to_standard, FROM_FORMAT, TO_FORMAT, from_text, to_text, split2segments
from ucca.core import Passage
from ucca.textutil import indent_xml


def file2passage(filename):
    """Opens a file and returns its parsed Passage object
    Tries to read both as a standard XML file and as a binary pickle
    :param filename: file name to write to
    """
    try:
        with open(filename) as f:
            etree = ElementTree().parse(f)
        return from_standard(etree)
    except Exception as e:
        try:
            with open(filename, 'rb') as h:
                return pickle.load(h)
        except Exception:
            raise e


def passage2file(passage, filename, indent=True, binary=False):
    """Writes a UCCA passage as a standard XML file or a binary pickle
    :param passage: passage object to write
    :param filename: file name to write to
    :param indent: whether to indent each line
    :param binary: whether to write pickle format (or XML)
    """
    if binary:
        with open(filename, 'wb') as h:
            pickle.dump(passage, h)
    else:  # xml
        root = to_standard(passage)
        xml = tostring(root).decode()
        output = indent_xml(xml) if indent else xml
        with open(filename, 'w') as h:
            h.write(output)


class LazyLoadedPassages(object):
    """
    Iterable interface to Passage objects that loads files on-the-go and can be iterated more than once
    """
    def __init__(self, files, sentences=False, paragraphs=False, default_converter=None):
        self.files = files
        self.sentences = sentences
        self.paragraphs = paragraphs
        self.split = self.sentences or self.paragraphs
        self.default_converter = default_converter
        self._files_iter = None
        self._split_iter = None
        self._file_handle = None
        self._next_index = None

    def __iter__(self):
        self._next_index = 0
        self._files_iter = iter(self.files)
        self._split_iter = None
        self._file_handle = None
        return self

    def __next__(self):
        passage = self._next_passage()
        self._next_index += 1
        return passage

    def _next_passage(self):
        passage = None
        if self._split_iter is None:
            try:
                file = next(self._files_iter)
            except StopIteration:  # Finished iteration
                raise
            if isinstance(file, Passage):  # Not really a file, but a Passage
                passage = file
            else:  # A file
                attempts = 3
                while not os.path.exists(file):
                    if attempts == 0:
                        print("File not found: %s" % file, file=sys.stderr)
                        return next(self)
                    print("Failed reading %s, trying %d more times..." % (file, attempts), file=sys.stderr)
                    time.sleep(5)
                    attempts -= 1
                try:
                    passage = file2passage(file)  # XML or binary format
                except (IOError, ParseError):  # Failed to read as passage file
                    base, ext = os.path.splitext(os.path.basename(file))
                    converter = FROM_FORMAT.get(ext.lstrip("."), self.default_converter or from_text)
                    self._file_handle = open(file)
                    self._split_iter = iter(converter(self._file_handle, passage_id=base, split=self.split))
            if self.split and self._split_iter is None:  # If it's not None, it's a converter and it splits alone
                self._split_iter = iter(split2segments(passage, is_sentences=self.sentences))
        if self._split_iter is not None:  # Either set before or initialized now
            try:
                # noinspection PyTypeChecker
                passage = next(self._split_iter)
            except StopIteration:  # Finished this converter
                self._split_iter = None
                if self._file_handle is not None:
                    self._file_handle.close()
                    self._file_handle = None
                return next(self)
        return passage

    # The following three methods are implemented to support shuffle;
    # note files are shuffled but there is no shuffling within files, as it would not be efficient.
    # Note also the inconsistency because these access the files while __iter__ accesses individual passages.
    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        return self.files[i]

    def __setitem__(self, i, value):
        self.files[i] = value

    def __bool__(self):
        return bool(self.files)


def read_files_and_dirs(files_and_dirs, sentences=False, paragraphs=False, default_converter=None):
    """
    :param files_and_dirs: iterable of files and/or directories to look in
    :param sentences: whether to split to sentences
    :param paragraphs: whether to split to paragraphs
    :param default_converter: input format converter to use if not clear from the file extension
    :return: list of (lazy-loaded) passages from all files given,
             plus any files directly under any directory given
    """
    files = list(files_and_dirs)
    files += [os.path.join(d, f) for d in files if os.path.isdir(d) for f in os.listdir(d)]
    files = [f for f in files if not os.path.isdir(f)]
    return LazyLoadedPassages(files, sentences, paragraphs, default_converter)


def write_passage(passage, output_format, binary, outdir, prefix, default_converter=None):
    suffix = output_format or ("pickle" if binary else "xml")
    outfile = outdir + os.path.sep + prefix + passage.ID + "." + suffix
    print("Writing passage '%s'..." % outfile)
    if output_format is None or output_format in ("pickle", "xml"):
        passage2file(passage, outfile, binary=binary)
    else:
        converter = TO_FORMAT.get(output_format, default_converter or to_text)
        output = "\n".join(line for line in converter(passage))
        with open(outfile, "w") as f:
            f.write(output + "\n")
