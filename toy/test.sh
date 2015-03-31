#!/usr/bin/env bash

python3 ../scripts/standard_to_conll.py toy.xml || exit 1
python3 ../scripts/conll_to_standard.py ucca_passage504.conll || exit 1
python3 ../private/evaluate.py -fr toy.xml -g ucca_passage504.xml || exit 1