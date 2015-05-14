#!/usr/bin/env bash

python3 ../scripts/standard_to_conll.py ../doc/toy.xml || exit 1
python3 ../scripts/conll_to_standard.py ucca_passage504.conll || exit 1
python3 ../scripts/evaluate.py -fr ../doc/toy.xml -g ucca_passage504.xml || exit 1
