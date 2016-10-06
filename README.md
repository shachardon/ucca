Universal Conceptual Cognitive Annotation [![Build Status](https://travis-ci.org/danielhers/ucca.svg?branch=master)](https://travis-ci.org/danielhers/ucca)
============================
UCCA is a novel linguistic framework for semantic annotation, whose details
are available at [the following paper][1]:

    Universal Conceptual Cognitive Annotation (UCCA)
    Omri Abend and Ari Rappoport, ACL 2013

This Python3-only package provides an API to the UCCA annotation and tools to
manipulate and process it. Its main features are conversion between different
representations of UCCA annotations, and rich objects for all of the linguistic
relations which appear in the theoretical framework (see `core`, `layer0`, `layer1`
and `convert` modules under the `ucca` package).

Running the parser:
-------------------

Install the required modules and NLTK models:

    virtualenv --python=/usr/bin/python3 .
    . bin/activate  # on bash
    source bin/activate.csh  # on csh
    pip install -r requirements.txt
    python -m nltk.downloader averaged_perceptron_tagger punkt
    python setup.py install

Download and extract the pre-trained models:

    wget http://www.cs.huji.ac.il/~danielh/ucca/{sparse,dense,nn}.tgz
    tar xvzf sparse.tgz
    tar xvzf dense.tgz
    tar xvzf nn.tgz

Run the parser on a text file (here named `example.txt`) using either of the models:

    python parsing/parse.py -sCLM example.txt -c sparse -m models/ucca-sparse
    python parsing/parse.py -sCLM example.txt -c dense -m models/ucca-dense
    python parsing/parse.py -sCLM example.txt -c nn -m models/ucca-nn

A file named `example.xml` will be created.


See [`ucca/README.md`](ucca/README.md) for a list of modules under the `ucca` package.

The `scripts` package contains various utilities for processing passage files.

The `parsing` package contains code for a full UCCA parser, currently under construction.

Authors
------
* Amit Beka: amit.beka@gmail.com
* Daniel Hershcovich: danielh@cs.huji.ac.il


License
-------
This package is licensed under the GPLv3 or later license (see [`LICENSE.txt`](master/LICENSE.txt)).

[1]: http://homepages.inf.ed.ac.uk/oabend/papers/ucca_acl.pdf
