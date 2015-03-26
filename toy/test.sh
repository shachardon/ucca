#!/usr/bin/env bash

python3 ../scripts/standard_to_conll.py toy.xml
python3 ../scripts/conll_to_standard.py ucca_passage504.conll
python3 ../private/evaluate.py -f -r toy.xml -g ucca_passage504.xml